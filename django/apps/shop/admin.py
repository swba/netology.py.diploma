from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RelatedDropdownFilter

from .models import Category, Seller, Product, ProductParameter, ShippingAddress, Order, OrderLineItem
from ..base.admin import ShowPhoneMixin


@admin.register(Seller)
class SellerAdmin(ModelAdmin):
    list_display = ('user', 'title', 'website_url', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)
    fields = ('user', 'title', 'website_url', 'is_active')
    compressed_fields = True
    warn_unsaved_form = True


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('title', 'slug')
    search_fields = ('title', 'slug')
    fields = ('title',)
    compressed_fields = True
    warn_unsaved_form = True


class ProductParameterInline(TabularInline):
    model = ProductParameter
    hide_title = True


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('title', 'slug', 'category', 'seller', 'quantity')
    search_fields = ('title', 'slug')
    list_filter = (
        ('category', RelatedDropdownFilter),
        ('seller', RelatedDropdownFilter),
    )
    fields = ('title', 'category', 'seller', 'external_id', 'model', 'quantity',
              'price', 'list_price')
    inlines = (ProductParameterInline,)
    compressed_fields = True
    warn_unsaved_form = True


@admin.register(ShippingAddress)
class ShippingAddressAdmin(ModelAdmin, ShowPhoneMixin):
    list_display = ('__str__', 'show_phone')
    compressed_fields = True
    warn_unsaved_form = True


class OrderLineItemInline(TabularInline):
    model = OrderLineItem
    hide_title = True


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    model = Order
    inlines = (OrderLineItemInline,)
    compressed_fields = True
    warn_unsaved_form = True
