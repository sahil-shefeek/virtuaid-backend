import uuid
import random
import string
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.validators import EmailValidator
from django.db import models

from backend import settings


class InterfaceUserManager(BaseUserManager):
    def _generate_unique_username(self, base_username):
        # Append random digits to ensure uniqueness
        while True:
            random_suffix = "".join(random.choices(string.digits, k=4))
            username = f"{base_username}{random_suffix}"
            if not self.model.objects.filter(username=username).exists():
                return username

    def create_user(self, email, name=None, password=None, **extra_fields):
        """
        This method is intentionally designed to raise an error since all users should be created 
        with specific role-based methods.
        Use create_superadmin, create_admin, or create_manager instead.
        """
        role = extra_fields.get('role', None)
        
        if role == 'superadmin':
            return self.create_superadmin(email=email, name=name, password=password)
        elif role == 'admin':
            created_by = extra_fields.get('created_by', None)
            return self.create_admin(email=email, name=name, password=password, created_by=created_by)
        elif role == 'manager':
            created_by = extra_fields.get('created_by', None)
            return self.create_manager(email=email, name=name, password=password, created_by=created_by)
        else:
            raise ValueError(
                "Generic create_user is not supported. Use create_superadmin, create_admin, or create_manager instead."
            )

    def create_admin(self, email, name, password=None, created_by=None, username=None, avatar=None):
        if not email:
            raise ValueError('Admin must have an email address')
        if not name:
            raise ValueError('Admin must have a name')
            
        if not username:
            # Generate a unique username from the email
            base_username = email.split("@")[0]
            username = self._generate_unique_username(base_username)
            
        user = self.model(email=self.normalize_email(email), name=name, created_by=created_by, username=username, avatar=avatar)
        user.set_password(password)
        user.save(using=self._db)
        user.groups.add(Group.objects.get(name='Admin'))
        user.save(using=self._db)
        return user

    def create_superadmin(self, email, name, password, username=None, avatar=None):
        if not email:
            raise ValueError('SuperAdmin must have an email address')
        if not name:
            raise ValueError('SuperAdmin must have a name')
            
        if not username:
            base_username = email.split("@")[0]
            username = self._generate_unique_username(base_username)
            
        user = self.model(email=self.normalize_email(email), name=name, username=username, avatar=avatar)
        user.set_password(password)
        user.save(using=self._db)
        user.groups.add(Group.objects.get(name='SuperAdmin'))
        user.save(using=self._db)
        return user

    def create_manager(self, email, name, password=None, created_by=None, username=None, avatar=None):
        if not email:
            raise ValueError('Manager must have an email address')
        if not name:
            raise ValueError('Manager must have a name')
            
        if not username:
            base_username = email.split("@")[0]
            username = self._generate_unique_username(base_username)
            
        user = self.model(email=self.normalize_email(email), name=name, created_by=created_by, username=username, avatar=avatar)
        user.set_password(password)
        user.save(using=self._db)
        user.groups.add(Group.objects.get(name='Manager'))
        user.save(using=self._db)
        return user


class InterfaceUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()]
    )
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    name = models.CharField(max_length=125)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='created_users')
    objects = InterfaceUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name

    def has_perm(self, perm, obj=None):
        if self.is_superadmin:
            return True  # Superusers have all permissions
            # Check for group-based permissions
            # Get the content type for the object or the 'auth' app if no object is provided
        if obj is not None:
            content_type = ContentType.objects.get_for_model(obj)
        else:
            content_type = ContentType.objects.get(app_label='auth', model='permission')

            # Check if any of the user's groups have the specified permission
        group_permissions = self.groups.filter(
            permissions__codename=perm,
            permissions__content_type=content_type
        ).exists()

        if group_permissions:
            return True

        # Default to built-in permission checks
        return super().has_perm(perm, obj)

    @property
    def is_admin(self):
        return self.groups.filter(name='Admin').exists()

    @property
    def is_superadmin(self):
        return self.groups.filter(name='SuperAdmin').exists()

    @property
    def is_manager(self):
        return self.groups.filter(name='Manager').exists()
