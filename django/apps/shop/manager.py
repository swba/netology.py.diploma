from django.db import models


class ProductCardManager(models.Manager):
    """Product card manager that adds product to all queries."""

    def get_queryset(self):
        return super().get_queryset().select_related(
            'product',
            'product__category'
        )


class OrderLineItemManager(models.Manager):
    """Order line item manager that adds product to all queries."""

    def get_queryset(self):
        return super().get_queryset().select_related(
            'product_card',
            'product_card__product'
        )
