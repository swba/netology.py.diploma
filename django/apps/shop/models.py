from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models import LoggableModel, PhoneField
from apps.base.utils import slugify

from .manager import ProductManager, LineItemManager, CategoryManager


class BaseShopModel(LoggableModel):
    """Abstract loggable shop model."""

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
        max_length=80,
        verbose_name=_("Title"))
    slug = models.SlugField(
        max_length=100,
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

    objects = CategoryManager()

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

    Unlike categories, products belong to specific sellers.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Category"))
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Seller"))
    external_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name=_("External ID"))
    model = models.CharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name=_("Model"))
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Quantity"))
    price = models.PositiveIntegerField(
        verbose_name=_("Price"))
    list_price = models.PositiveIntegerField(
        verbose_name=_("List Price"))

    objects = ProductManager()

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ('title',)
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'slug'],
                name='unique_product'),
        ]

    def save(self, *args, **kwargs):
        # Add unique seller ID to the product slug.
        self.slug = slugify(self.title) + f"-{self.seller.pk}"
        super().save(*args, **kwargs)


class ProductParameter(models.Model):
    """Custom product parameter."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='parameters',
        verbose_name=_("Product"))
    name = models.CharField(
        max_length=50,
        verbose_name=_("Name"))
    value = models.CharField(
        max_length=100,
        verbose_name=_("Value"))

    class Meta:
        verbose_name = _("Product Parameter")
        verbose_name_plural = _("Product Parameters")
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('product', 'name'),
                name='unique_product_parameter')
        ]

    def __str__(self):
        return self.name


class Order(BaseShopModel):
    """Customer's order."""

    class Status(models.TextChoices):
        PENDING = 'Pending', _("Pending")
        CONFIRMED = 'Confirmed', _("Confirmed")
        SHIPPING = 'Shipping', _("Shipping")
        COMPLETED = 'Completed', _("Completed")
        CANCELED = 'Canceled', _("Canceled")

    seller = models.ForeignKey(
        Seller,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_("Seller"))
    shipping_address = models.ForeignKey(
        ShippingAddress,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_("Shipping Address"))
    status = models.CharField(
        max_length=10,
        choices=Status,
        default=Status.PENDING)

    status_workflow = {
        Status.PENDING: (Status.CONFIRMED, Status.CANCELED),
        Status.CONFIRMED: (Status.SHIPPING, Status.CANCELED),
        Status.SHIPPING: (Status.COMPLETED, Status.CANCELED,),
        Status.COMPLETED: (),
        Status.CANCELED: ()
    }

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ('-created_at',)

    def __str__(self):
        return _("Order from {date}").format(date=self.created_at.date())


class BaseLineItem(models.Model):
    """Base abstract model for order and cart line items.

    A line item is just a pair of a product and its quantity.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name=_("Product"))
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity"))

    objects = LineItemManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.product.title

    @property
    def total(self):
        """Line item total."""
        return self.product.list_price * self.quantity


class OrderLineItem(BaseLineItem):
    """Line item to be used in orders."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='line_items',
        verbose_name=_("Order"))

    class Meta:
        verbose_name = _("Order Line Item")
        verbose_name_plural = _("Order Line Items")
        constraints = [
            models.UniqueConstraint(
                fields=('order', 'product'),
                name='unique_order_product')
        ]

    def clean(self):
        super().clean()

        # Ensure product belongs to the order's seller.
        if self.product.seller.pk != self.order.seller.pk:
            raise ValidationError(
                _("Product seller must match the order seller.")
            )


class CartLineItem(BaseLineItem):
    """Line item to be used in customer carts."""

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_("User"))

    class Meta:
        verbose_name = _("Cart Line Item")
        verbose_name_plural = _("Cart Line Items")
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'product'),
                name='unique_user_product')
        ]
        ordering = ('id',)
