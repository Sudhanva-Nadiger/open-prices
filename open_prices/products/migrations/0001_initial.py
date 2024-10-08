# Generated by Django 5.1 on 2024-09-03 16:18

import django.contrib.postgres.fields
import django.utils.timezone
import openfoodfacts.types
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(unique=True)),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        choices=[
                            (
                                openfoodfacts.types.Flavor["off"],
                                openfoodfacts.types.Flavor["off"],
                            ),
                            (
                                openfoodfacts.types.Flavor["obf"],
                                openfoodfacts.types.Flavor["obf"],
                            ),
                            (
                                openfoodfacts.types.Flavor["opff"],
                                openfoodfacts.types.Flavor["opff"],
                            ),
                            (
                                openfoodfacts.types.Flavor["opf"],
                                openfoodfacts.types.Flavor["opf"],
                            ),
                            (
                                openfoodfacts.types.Flavor["off_pro"],
                                openfoodfacts.types.Flavor["off_pro"],
                            ),
                        ],
                        max_length=10,
                        null=True,
                    ),
                ),
                ("source_last_synced", models.DateTimeField(blank=True, null=True)),
                ("product_name", models.CharField(blank=True, null=True)),
                ("image_url", models.CharField(blank=True, null=True)),
                ("product_quantity", models.IntegerField(blank=True, null=True)),
                ("product_quantity_unit", models.CharField(blank=True, null=True)),
                (
                    "categories_tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                ("brands", models.CharField(blank=True, null=True)),
                (
                    "brands_tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "labels_tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                ("nutriscore_grade", models.CharField(blank=True, null=True)),
                ("ecoscore_grade", models.CharField(blank=True, null=True)),
                ("nova_group", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "unique_scans_n",
                    models.PositiveIntegerField(blank=True, default=0, null=True),
                ),
                (
                    "price_count",
                    models.PositiveIntegerField(blank=True, default=0, null=True),
                ),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
                "db_table": "products",
            },
        ),
    ]
