from django.db import models


class EncryptedSecretField(models.CharField):
    """Historical migration compatibility only.

    MFA was removed from Mhami. Django still imports this class while replaying
    the old migration chain before the following migration drops its table.
    """
