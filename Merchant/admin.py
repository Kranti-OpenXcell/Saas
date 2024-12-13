from django.contrib import admin
from .models import Client
from django_tenants.admin import TenantAdminMixin


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = ('name', 'paid_until')



# Register your models here.
