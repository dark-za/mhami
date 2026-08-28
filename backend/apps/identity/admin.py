from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import MfaEnrollment, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    ordering = ("login_id",)
    list_display = ("login_id", "display_name", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("login_id", "password")}),
        ("Identity", {"fields": ("display_name",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("login_id", "display_name", "password1", "password2", "is_staff", "is_active"),
        }),
    )


@admin.register(MfaEnrollment)
class MfaEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "method_type", "label", "verified_at", "active")
    search_fields = ("user__login_id", "label", "credential_id")
