from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.base.models import LoggableModel, PhoneField, DeletableModel

from .manager import ProductCardManager, OrderLineItemManager


class BaseShopModel(LoggableModel, DeletableModel):
    """Abstract loggable and deletable model."""

    class Meta:
        abstract = True


class ShippingAddress(BaseShopModel):
    """Customer's shipping address."""

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='shipping_addresses',
        verbose_name=_("User"))
    full_name = models.CharField(
        max_length=255,
        verbose_name=_("Full Name"),
        help_text=_("Full recipient's name."))
    phone_number = PhoneField(
        verbose_name=_("Phone Number"),
        help_text=_("Phone number in international format, e.g. +79991112233."),)
    street_address = models.CharField(
        max_length=255,
        verbose_name=_("Street Address"),
        help_text=_("Includes the building name/number and street name, as well as apartment or unit number."))
    locality = models.CharField(
        max_length=255,
        verbose_name=_("Locality"),
        help_text=_("The city, town, or village where the address is located."))
    administrative_area = models.CharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name=_("Administrative Area"),
        help_text=_("A larger administrative area such as a state, province, region, or district."))
    postal_code = models.CharField(
        max_length=10,
        verbose_name=_("Postal Code"),
        help_text=_("A numeric or alphanumeric code for mail sorting and delivery."))
    country = models.CharField(
        max_length=100,
        verbose_name=_("Country"),
        help_text=_("The name of the destination country."))

    class Meta:
        verbose_name = _("Shipping Address")
        verbose_name_plural = _("Shipping Addresses")
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.full_name}\n{self.street_address}\n{self.locality}, {self.country}"


class Seller(BaseShopModel):
    """Seller's profile."""

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='sellers',
        verbose_name=_("Seller"))
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"))
    website_url = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Website URL"))
    business_info = models.TextField(
        verbose_name=_("Business Information"))
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Activity Status"),
        help_text=_("Whether the seller is active and accepts orders."))

    class Meta:
        verbose_name = _("Seller Profile")
        verbose_name_plural = _("Seller Profiles")
        ordering = ('-created_at',)

    def __str__(self):
        return self.title


class BaseCatalogModel(BaseShopModel):
    """Base abstract model for categories and products."""

    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"))
    slug = models.SlugField(
        verbose_name=_("Slug"))

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Category(BaseCatalogModel):
    """Product category.

    Product categories are global, i.e. do not belong to any seller.
    """

    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")
        ordering = ('title',)
        constraints = [
            models.UniqueConstraint(
                fields=('slug',),
                name='unique_category')
        ]


class Product(BaseCatalogModel):
    """Base product model.

    Base product cards are global, i.e. do not belong to any seller.
    This model contains only the very base product information; more
    product data (related to a seller, though) can be found in the
    ProductCard model.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Category"))

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ('title',)
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'slug'],
                name='unique_product'),
        ]


class ProductCard(BaseShopModel):
    """Product card model.

    Unlike categories and products, product cards belong to specific
    sellers.
    """

    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Seller"))
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cards',
        verbose_name=_("Product"))
    external_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name=_("External ID"))
    code = models.CharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name=_("Code"))
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Quantity"))
    price = models.PositiveIntegerField(
        verbose_name=_("Price"))
    list_price = models.PositiveIntegerField(
        verbose_name=_("List Price"))

    objects = ProductCardManager()

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ('product__title',)
        constraints = [
            models.UniqueConstraint(
                fields=['seller', 'product'],
                name='unique_seller_product'),
        ]

    def __str__(self):
        return self.product.title


class ProductParameter(models.Model):
    """Custom product parameter."""

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Parameter Name"))

    class Meta:
        verbose_name = _("Product Parameter")
        verbose_name_plural = _("Product Parameters")
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductCardParameterValue(models.Model):
    """Custom product card parameter value."""

    parameter = models.ForeignKey(
        ProductParameter,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_("Parameter"))
    product_card = models.ForeignKey(
        ProductCard,
        on_delete=models.CASCADE,
        related_name='parameters',
        verbose_name=_("Product Card"))
    value = models.CharField(
        max_length=100,
        verbose_name=_("Value"))

    class Meta:
        verbose_name = _("Product Parameter Value")
        verbose_name_plural = _("Product Parameter Values")
        constraints = [
            models.UniqueConstraint(
                fields=('parameter', 'product_card'),
                name='unique_product_parameter')
        ]

    def __str__(self):
        return self.value


class Order(BaseShopModel):
    """Customer's order."""

    class OrderStatus(models.TextChoices):
        PENDING = 'Pending', _('Pending')
        CONFIRMED = 'Confirmed', _('Confirmed')
        SHIPPING = 'Shipping', _('Shipping')
        COMPLETED = 'Completed', _('Completed')
        CANCELED = 'Canceled', _('Canceled')

    shipping_address = models.ForeignKey(
        ShippingAddress,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_("Shipping Address"))
    status = models.CharField(
        max_length=10,
        choices=OrderStatus,
        default=OrderStatus.PENDING)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ('-created_at',)

    def __str__(self):
        return _("Order from {date}").format(date=self.created_at.date())


class OrderLineItem(models.Model):
    """Order line item is a pair of a product card and its quantity."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='line_items',
        verbose_name=_("Order"))
    product_card = models.ForeignKey(
        ProductCard,
        on_delete=models.CASCADE,
        related_name='order_line_items',
        verbose_name=_("Product Card"))
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity"))

    objects = OrderLineItemManager()

    class Meta:
        verbose_name = _("Order Line Item")
        verbose_name_plural = _("Order Line Items")

    def __str__(self):
        return self.product_card.product.title

    @property
    def total(self):
        return self.product_card.list_price * self.quantity
