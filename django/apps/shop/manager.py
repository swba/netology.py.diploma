from django.core.paginator import Paginator
from django.db import models
from rest_framework.settings import api_settings


class PaginatorQuerySet(models.QuerySet):
    """Custom query set that adds pagination support."""

    def paginate(self, page_size: int = api_settings.PAGE_SIZE):
        return Paginator(self, page_size)


class ProductManager(models.Manager):
    """Product manager that adds category to all queries."""

    def get_queryset(self):
        return PaginatorQuerySet(self.model).select_related('category')


class LineItemManager(models.Manager):
    """Line item manager that adds product to all queries."""

    def get_queryset(self):
        return super().get_queryset().select_related('product')
