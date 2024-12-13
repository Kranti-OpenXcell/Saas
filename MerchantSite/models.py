from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class Customer(models.Model):
    customer_id = models.CharField(primary_key=True, editable=False)
    merchant_id = models.ForeignKey('Merchant.Client', on_delete=models.CASCADE, related_name='merchants')
    name = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    channels = models.CharField(max_length=50)  # This is not part of the relation
    tickets_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name
  
# Custom User Manager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        Create and return a superuser with an email, username, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('role', 'merchant')  # Superuser can be treated as a merchant by default

        return self.create_user(email, username, password, **extra_fields)

# Role Choices
class UserRole(models.TextChoices):
    MERCHANT = 'merchant', 'Merchant'
    CUSTOMER = 'customer', 'Customer'

# Custom User Model
class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Admin user flag
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER
    )  # New role field with two options (merchant, customer)

    # Optional: You can add more fields here, such as profile picture, etc.

    # Set the custom manager
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'  # Use email as the unique identifier
    REQUIRED_FIELDS = ['username']  # Username is required for user creation

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_superuser or super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        return self.is_superuser or super().has_module_perms(app_label)


class Ticket(models.Model):
    TICKET_PRIORITIES = [
        ('1', 'Low'),
        ('2', 'High'),
    ]

    TICKET_CHANNELS = [
        ('Twitter', 'Twitter'),
        ('Instagram', 'Instagram'),
        ('Email', 'Email'),
        ('WhatsApp', 'WhatsApp'),
    ]

    TICKET_STATUS = [
        ('open', 'Open'),
        ('deferred', 'Deferred'),
        ('closed', 'Closed'),
    ]

    ticket_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant_id = models.ForeignKey(
        'Merchant.Client',
        on_delete=models.CASCADE,
        related_name='tickets_related'  # Unique related_name for Ticket
    )
    customer_id = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='customer_tickets'  # Unique related_name for customer in Channel
    )    
    subject = models.TextField()
    priority = models.CharField(max_length=1, choices=TICKET_PRIORITIES)
    channel = models.CharField(max_length=10, choices=TICKET_CHANNELS)
    status = models.CharField(max_length=10, choices=TICKET_STATUS)
    response_recap = models.TextField(null=True, blank=True)
    deferred_at = models.DateTimeField(null=True, blank=True)
    closed_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.subject

# Updated KnowledgeBase model
class KnowledgeBase(models.Model):
    kb_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant_id = models.ForeignKey('Merchant.Client', on_delete=models.CASCADE, related_name='knowledge_bases')
    customer_id = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='knowledge_bases')
    name = models.CharField(max_length=255)
    version = models.IntegerField(default=1)
    file_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Channel(models.Model):
    CHANNEL_NAMES = [
        ('Twitter', 'Twitter'),
        ('Instagram', 'Instagram'),
        ('Email', 'Email'),
        ('WhatsApp', 'WhatsApp'),
    ]

    channel_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant_id = models.ForeignKey(
        'Merchant.Client',
        on_delete=models.CASCADE,
        related_name='channels_related'  # Unique related_name for Channel
    )
    customer_id = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='customer_channels'  # Unique related_name for customer in Channel
    )
    name = models.CharField(max_length=10, choices=CHANNEL_NAMES)
    account_name = models.CharField(max_length=255)
    account_password = models.CharField(max_length=255)
    channel_active_status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
