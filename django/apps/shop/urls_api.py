from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views_api import (
    ProductViewSet,
    CartLineItemViewSet,
    ShippingAddressViewSet
)

app_name = 'api.shop'

product_router = DefaultRouter()
product_router.register('', ProductViewSet)

cart_router = DefaultRouter()
cart_router.register('', CartLineItemViewSet)

shipping_address_router = DefaultRouter()
shipping_address_router.register('', ShippingAddressViewSet)

urlpatterns = [
    path('products/', include(product_router.urls)),
    path('cart/', include(cart_router.urls)),
    path('shipping-addresses/', include(shipping_address_router.urls)),
]
