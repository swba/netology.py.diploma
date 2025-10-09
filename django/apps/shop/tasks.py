from celery import shared_task

from apps.shop.models import Product, ProductParameter
from apps.shop.serializers import ProductCreateSerializer


@shared_task
def catalog_import_task(seller_id: int, products: list):
    """Imports products for a seller.

    Args:
        seller_id: Seller ID.
        products: List of dicts of product data as returned by
            ProductImportSerializer.
    """
    for data in products: # type: dict
        # Get existing product, if any.
        product = data.pop('id', None)
        if not product and 'external_id' in data:
            product = Product.objects.get_or_none(
                seller_id=seller_id,
                external_id=data.get('external_id')
            )

        # Get the category. Category fields are already validated by
        # the serializer, so it's guaranteed that category exists.
        # Also, we don't need category fields anymore, so remove them.
        category = None
        for key in ('category_id', 'category_slug', 'category_title'):
            if key in data:
                category = data.pop(key)

        # Add fields required by ProductCreateSerializer.
        data['seller'] = seller_id
        data['category'] = category.pk

        # We can finally save the product.
        serializer = ProductCreateSerializer(instance=product, data=data)
        # Extract parameters as they should be saved independently of
        # the parent product.
        parameters = data.pop('parameters', {})
        # Validation should always be OK as this is actually the second
        # time we validate (almost) the same data with the same
        # serializer (this task gets already validated data).
        if serializer.is_valid(raise_exception=True):
            product = serializer.save()
            # Now handle the parameters.
            for name, value in parameters.items():
                ProductParameter.objects.update_or_create(
                    name=name,
                    product=product,
                    defaults={'value': value}
                )
