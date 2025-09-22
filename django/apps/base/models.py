from django.db import models
from django.utils import timezone


class LoggableModel(models.Model):
    """Abstract model providing created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DeletableModel(models.Model):
    """Abstract model providing is_deleted and deleted_at fields."""

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def mark_as_deleted(self, is_deleted=True):
        """Marks the object as deleted.

        Args:
            is_deleted: Whether to mark instance as deleted. Defaults to True.
        """
        if self.is_deleted ^ is_deleted: # Check if the flag is to be changed.
            self.is_deleted = is_deleted
            if is_deleted:
                self.deleted_at = timezone.now()
            else:
                self.deleted_at = None
            self.save(update_fields=['is_deleted', 'deleted_at'])