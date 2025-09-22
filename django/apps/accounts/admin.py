from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as BaseGroup
from django.utils.translation import gettext_lazy as _

from unfold.forms import AdminPasswordChangeForm, UserCreationForm, UserChangeForm
from unfold.admin import ModelAdmin

from .models import User, Group


admin.site.unregister(BaseGroup)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_("Personal info"), {'fields': ('first_name', 'last_name')}),
        (
            _("Permissions"),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (_("Important dates"), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ("email", 'usable_password', 'password1', 'password2'),
            },
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)

    compressed_fields = True
