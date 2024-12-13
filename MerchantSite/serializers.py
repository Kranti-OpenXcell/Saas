from rest_framework import serializers
from MerchantSite.models import Customer,CustomUser,Ticket,Channel,KnowledgeBase
from Merchant.models import Client
import uuid
from django_tenants.utils import schema_context
from Merchant.models import Client


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer model with comprehensive validation
    """
    customer_id = serializers.UUIDField(read_only=True)
    merchant_id = serializers.PrimaryKeyRelatedField(  # Fixed typo here
        queryset=Client.objects.all(),
        write_only=True
    )
    
    class Meta:
        model = Customer
        fields = [
            'customer_id', 
            'merchant_id',  # Fixed typo here
            'name', 
            'account_name', 
            'channels', 
            'tickets_count',
            'created_at',
            'updated_at',
            'is_deleted'
        ]
        read_only_fields = ['created_at', 'updated_at']

class CustomerBulkCreateSerializer(serializers.Serializer):

    """
    Serializer for bulk customer creation
    """
    schema_name = serializers.CharField(required=True)
    num_records = serializers.IntegerField(
        required=False, 
        default=10, 
        min_value=1, 
        max_value=1000
    )
    tenant_id = serializers.UUIDField(required=False)

    def validate_schema_name(self, value):
        """
        Validate that the schema name exists
        """
        

        with schema_context('public'):
            if not Client.objects.filter(schema_name=value).exists():
                raise serializers.ValidationError(f"No tenant found with schema name: {value}")
        return value
    
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']

    def create(self, validated_data):
        """
        Create a new CustomUser instance with password handling.
        """
        # Remove the password from validated_data as it's handled separately
        password = validated_data.pop('password', None)

        user = CustomUser.objects.create_user(
             # Pass the password separately
            **validated_data  # Pass the other fields
        )
        return user

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'  # Include all fields or specify a list of fields if necessary

class ChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for Channel model with comprehensive validation
    """
    class Meta:
        model = Channel
        fields = '__all__'  # Include all fields or specify a list of fields if necessary


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """
    Serializer for KnowledgeBase model with validation
    """

    class Meta:
        model = KnowledgeBase
        fields = '__all__'  # Include all fields or specify a list of fields if necessary
        read_only_fields = ['kb_id', 'created_at', 'last_modified_at']
