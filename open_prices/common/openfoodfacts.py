import datetime

import requests
import tqdm
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from openfoodfacts import (
    API,
    APIVersion,
    Country,
    DatasetType,
    Environment,
    Flavor,
    ProductDataset,
)
from openfoodfacts.images import generate_image_url
from openfoodfacts.types import JSONType

OFF_FIELDS = [
    "product_name",
    "product_quantity",
    "product_quantity_unit",
    "categories_tags",
    "brands",
    "brands_tags",
    "labels_tags",
    "image_url",
    "nutriscore_grade",
    "ecoscore_grade",
    "nova_group",
    "unique_scans_n",
]


def authenticate(username, password):
    data = {"user_id": username, "password": password, "body": 1}
    return requests.post(f"{settings.OAUTH2_SERVER_URL}", data=data)


def normalize_product_fields(product: JSONType) -> JSONType:
    """Normalize product fields and return a product dict
    ready to be inserted in the database.

    :param product: the product to normalize
    :return: the normalized product
    """
    product = product.copy()
    product_quantity = int(product.get("product_quantity") or 0)
    if product_quantity >= 100_000:
        # If the product quantity is too high, it's probably an
        # error, and may cause an OutOfRangeError in the database
        product["product_quantity"] = None
    return product


def generate_main_image_url(
    code: str, images: JSONType, lang: str, flavor: Flavor = Flavor.off
) -> str | None:
    """Generate the URL of the main image of a product.

    :param code: The code of the product
    :param images: The images of the product
    :param lang: The main language of the product
    :return: The URL of the main image of the product or None if no image is
      available.
    """
    image_key = None
    if f"front_{lang}" in images:
        image_key = f"front_{lang}"
    else:
        for key in (k for k in images if k.startswith("front_")):
            image_key = key
            break

    if image_key:
        image_rev = images[image_key]["rev"]
        image_id = f"{image_key}.{image_rev}.400"
        return generate_image_url(
            code, image_id=image_id, flavor=flavor, environment=Environment.org
        )

    return None


def get_product(code: str, flavor: Flavor = Flavor.off) -> JSONType | None:
    client = API(
        user_agent=settings.OFF_USER_AGENT,
        username=None,
        password=None,
        country=Country.world,
        flavor=flavor,
        version=APIVersion.v2,
        environment=Environment.org,
    )
    return client.product.get(code)


def get_product_dict(product, flavor=Flavor.off) -> JSONType | None:
    product_dict = dict()
    try:
        response = get_product(code=product.code, flavor=flavor)
        if response:
            product_dict["source"] = flavor
            for off_field in OFF_FIELDS:
                if off_field in response:
                    product_dict[off_field] = response[off_field]
            product_dict = normalize_product_fields(product_dict)
        return product_dict
    except Exception:
        # logger.exception("Error returned from Open Food Facts")
        return None


def import_product_db(flavor: Flavor = Flavor.off, batch_size: int = 1000) -> None:
    """Import from DB JSONL dump to create/update product table.

    :param db: the session to use
    :param batch_size: the number of products to create/update in a single
      transaction, defaults to 1000
    """
    from open_prices.products.models import Product

    print((f"Launching import_product_db ({flavor})"))
    existing_product_flavor_codes = set(
        Product.objects.filter(source=flavor).values_list("code", flat=True)
    )
    print(
        f"Number of existing Product codes (from {flavor}): {len(existing_product_flavor_codes)}"
    )
    dataset = ProductDataset(
        flavor=flavor,
        dataset_type=DatasetType.jsonl,
        force_download=True,
        download_newer=True,
    )

    seen_codes = set()
    products_to_create_or_update = list()
    added_count = 0
    updated_count = 0
    # the dataset was created after the start of the day, every product updated
    # after should be skipped, as we don't know the exact creation time of the
    # dump
    start_datetime = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        hour=0, minute=0, second=0
    )

    for product in tqdm.tqdm(dataset):
        # Skip products without a code, or with wrong code
        if ("code" not in product) or (not product["code"].isdigit()):
            continue
        product_code = product["code"]

        # Skip duplicate products
        if product_code in seen_codes:
            continue
        seen_codes.add(product_code)

        # Some products have no "lang" field (especially non-OFF products)
        product_lang = product.get("lang", product.get("lc", "en"))
        # Store images & last_modified_t
        product_images: JSONType = product.get("images", {})
        product_last_modified_t = product.get("last_modified_t")

        # Convert last_modified_t to a datetime object
        # (sometimes the field is a string, convert to int first)
        if isinstance(product_last_modified_t, str):
            product_last_modified_t = int(product_last_modified_t)
        product_source_last_modified = (
            datetime.datetime.fromtimestamp(
                product_last_modified_t, tz=datetime.timezone.utc
            )
            if product_last_modified_t
            else None
        )
        # Skip products that have no last_modified date
        if product_source_last_modified is None:
            continue

        # Skip products that have been modified today (more recent updates are
        # possible)
        if product_source_last_modified >= start_datetime:
            print(f"Skipping {product_code}")
            continue

        # Build product dict to create/update
        product_dict = {
            key: product[key] if (key in product) else None for key in OFF_FIELDS
        }
        product_dict["image_url"] = generate_main_image_url(
            product_code, product_images, product_lang, flavor=flavor
        )
        product_dict["source"] = flavor
        product_dict["source_last_synced"] = timezone.now()
        product_dict = normalize_product_fields(product_dict)

        # Case 1: new OFF product (not in OP database)
        if product_code not in existing_product_flavor_codes:
            product_dict["code"] = product_code
            products_to_create_or_update.append(Product(**product_dict))
            added_count += 1

        # Case 2: existing product (already in OP database)
        else:
            # Update the product if it:
            # - is part of the current flavor sync (or if it has no source (created in Open Prices before OFF))  # noqa
            # - has not been updated since the creation of the current dataset
            existing_product_qs = (
                Product.objects.filter(code=product_code)
                .filter(Q(source=flavor) | Q(source=None))
                .filter(
                    Q(source_last_synced__lt=product_source_last_modified)
                    | Q(source_last_synced=None)
                )
            )
            if existing_product_qs.exists():
                products_to_create_or_update.append(Product(**product_dict))
                updated_count += 1

        # update the database regularly
        if (
            len(products_to_create_or_update)
            and len(products_to_create_or_update) % batch_size == 0
        ):
            Product.objects.bulk_create(
                products_to_create_or_update,
                update_conflicts=True,
                update_fields=OFF_FIELDS,
                unique_fields=["code"],
            )
            print(f"Products: {added_count} added, {updated_count} updated")
            products_to_create_or_update = list()

    # final database update
    Product.objects.bulk_create(
        products_to_create_or_update,
        update_conflicts=True,
        update_fields=OFF_FIELDS,
        unique_fields=["code"],
    )
    print(f"Products: {added_count} added, {updated_count} updated. Done!")
