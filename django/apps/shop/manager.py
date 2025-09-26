from django.db import models


class ProductCardManager(models.Manager):
    """Product card manager that adds product to all queries."""

    def get_queryset(self):
        return super().get_queryset().select_related(
            'product',
            'product__category'
        )


class LineItemManager(models.Manager):
    """Line item manager that adds product to all queries."""

    def get_queryset(self):
        return super().get_queryset().select_related(
            'product_card',
            'product_card__product'
        )
