from __future__ import annotations

import uuid
from django.utils import timezone

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from .fields import EncryptedSecretField


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, login_id: str, password: str | None = None, **extra_fields):
        if not login_id:
            raise ValueError("login_id is required")
        user = self.model(login_id=login_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login_id: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(login_id, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login_id = models.CharField(max_length=150, unique=True)
    display_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "login_id"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.login_id


class MfaMethodType(models.TextChoices):
    TOTP = "totp", "TOTP"
    PASSKEY = "passkey", "Passkey"


class MfaEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mfa_enrollments")
    method_type = models.CharField(max_length=32, choices=MfaMethodType.choices)
    label = models.CharField(max_length=120, blank=True)
    secret = EncryptedSecretField(max_length=512, blank=True)
    credential_id = models.CharField(max_length=255, blank=True)
    public_key = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    last_used_timestep = models.BigIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user", "method_type", "active"])]

    @property
    def is_verified(self) -> bool:
        return self.verified_at is not None

    def verify(self) -> None:
        self.verified_at = timezone.now()
        self.save(update_fields=["verified_at", "updated_at"])
