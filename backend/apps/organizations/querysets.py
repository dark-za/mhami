from __future__ import annotations

from django.db.models import QuerySet


class BranchQuerySet(QuerySet):
    def visible_to(self, user):
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return self
        return self.filter(company__memberships__user=user, company__memberships__active=True)

