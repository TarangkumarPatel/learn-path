from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'name', 'email', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'name', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Profile', {'fields': ('name',)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('name',)}),
    )
