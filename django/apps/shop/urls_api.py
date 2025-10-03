from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views_api import (
    CategoryViewSet,
    ProductViewSet,
    CartLineItemViewSet,
    ShippingAddressViewSet,
    OrderViewSet,
    SellerViewSet,
)

app_name = 'api.shop'

seller_router = DefaultRouter()
seller_router.register('', SellerViewSet)

category_router = DefaultRouter()
category_router.register('', CategoryViewSet)

product_router = DefaultRouter()
product_router.register('', ProductViewSet)

cart_router = DefaultRouter()
cart_router.register('', CartLineItemViewSet)

shipping_address_router = DefaultRouter()
shipping_address_router.register('', ShippingAddressViewSet)

order_router = DefaultRouter()
order_router.register('', OrderViewSet)

urlpatterns = [
    path('sellers/', include(seller_router.urls)),
    path('categories/', include(category_router.urls)),
    path('products/', include(product_router.urls)),
    path('cart/', include(cart_router.urls)),
    path('shipping-addresses/', include(shipping_address_router.urls)),
    path('orders/', include(order_router.urls)),
]
