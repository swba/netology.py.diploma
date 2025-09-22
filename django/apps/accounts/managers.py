from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """A model manager for the User model without a username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Creates and saves a User given email and password."""
        if not email:
            raise ValueError("The email must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a regular User."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Creates and saves a SuperUser."""
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self._create_user(email, password, **extra_fields)
