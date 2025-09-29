from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from .filters import ProductFilter
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     GenericViewSet):
    """View set to retrieve products."""

    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    filterset_class = ProductFilter
