from django.core.paginator import Paginator
from django.db import models
from rest_framework.settings import api_settings


class GetOrNoneManager(models.Manager):
    """Base manager providing a get_or_none method."""

    def get_or_none(self, *args, **kwargs):
        """Returns None if self.get() raises an exception."""
        try:
            return self.get(*args, **kwargs)
        except (self.model.DoesNotExist, self.model.MultipleObjectsReturned):
            return None


class PaginatorQuerySet(models.QuerySet):
    """Custom query set that adds pagination support."""

    def paginate(self, page_size: int = api_settings.PAGE_SIZE):
        return Paginator(self, page_size)


class CategoryManager(GetOrNoneManager):
    """Category manager."""
    pass


class ProductManager(GetOrNoneManager):
    """Product manager that adds category to all queries."""

    def get_queryset(self):
        return PaginatorQuerySet(self.model).select_related('category')


class LineItemManager(models.Manager):
    """Line item manager that adds product to all queries."""

    def get_queryset(self):
        return super().get_queryset().select_related('product')
