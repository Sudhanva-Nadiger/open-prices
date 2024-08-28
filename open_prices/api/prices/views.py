from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from open_prices.api.prices.filters import PriceFilter
from open_prices.api.prices.serializers import (
    PriceCreateSerializer,
    PriceFullSerializer,
    PriceUpdateSerializer,
)
from open_prices.common.authentication import CustomAuthentication
from open_prices.prices.models import Price


class PriceViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]  # disable "put"
    queryset = Price.objects.all()
    serializer_class = PriceFullSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PriceFilter
    ordering_fields = ["price", "date", "created"]
    ordering = ["created"]

    def get_queryset(self):
        if self.request.method in ["PATCH", "DELETE"]:
            # only return prices owned by the current user
            if self.request.user.is_authenticated:
                return Price.objects.filter(owner=self.request.user.user_id)
        return self.queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PriceCreateSerializer
        elif self.request.method == "PATCH":
            return PriceUpdateSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user.user_id, source=self.source)

    def create(self, request: Request, *args, **kwargs):
        # validate
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # get source
        self.source = self.request.GET.get("app_name", "API")
        # save
        price = self.perform_create(serializer)
        # return full price
        return Response(
            self.serializer_class(price).data, status=status.HTTP_201_CREATED
        )
