from django.db import models


class ProductManager(models.Manager):
    """Product manager that adds category to all queries."""

    def get_queryset(self):
        return super().get_queryset().select_related('category')


class LineItemManager(models.Manager):
    """Line item manager that adds product to all queries."""

    def get_queryset(self):
        return super().get_queryset().select_related('product')
