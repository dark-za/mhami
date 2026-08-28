from __future__ import annotations

import hashlib

from rest_framework.settings import api_settings
from rest_framework.throttling import SimpleRateThrottle


class DynamicRateThrottle(SimpleRateThrottle):
    def get_rate(self):
        return api_settings.DEFAULT_THROTTLE_RATES[self.scope]


class RegistrationIPThrottle(DynamicRateThrottle):
    scope = "registration_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class LoginIPThrottle(DynamicRateThrottle):
    scope = "login_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class LoginAccountThrottle(DynamicRateThrottle):
    scope = "login_account"

    def get_cache_key(self, request, view):
        company_code = str(request.data.get("company_code", "")).strip().lower()
        login_id = str(request.data.get("login_id", "")).strip().lower()
        if not company_code or not login_id:
            return None
        identifier = hashlib.sha256(f"{company_code}:{login_id}".encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": identifier}


class MfaUserThrottle(DynamicRateThrottle):
    scope = "mfa_user"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None
        return self.cache_format % {"scope": self.scope, "ident": str(user.id)}
