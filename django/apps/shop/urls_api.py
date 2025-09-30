from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views_api import ProductViewSet, CartLineItemViewSet

app_name = 'api.shop'

product_router = DefaultRouter()
product_router.register('', ProductViewSet)

cart_router = DefaultRouter()
cart_router.register('', CartLineItemViewSet)

urlpatterns = [
    path('products/', include(product_router.urls)),
    path('cart/', include(cart_router.urls)),
]
