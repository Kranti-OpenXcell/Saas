
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction,connections
from Merchant.models import Client, Domain
from MerchantSite.models import Customer,CustomUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_tenants.utils import schema_context
import re
from django.http import JsonResponse,HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from django.db import transaction
from faker import Faker
import random
import uuid
from MerchantSite.serializers import CustomerSerializer, KnowledgeBaseSerializer,ChannelSerializer,CustomUserSerializer,TicketSerializer
from MerchantSite.task2 import send_async_email2

@method_decorator(csrf_exempt, name='dispatch')
class CreateTenantView(APIView):
    def post(self, request):
        try:
            # Ensure we're in the public schema
            with schema_context('public'):
                with transaction.atomic():
                    tenant_name = request.data.get('name')
                    domain_name = request.data.get('domain')
                    
                    # Validate input
                    if not tenant_name or not domain_name:
                        return Response({
                            'error': 'Both name and domain are required'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Sanitize schema name
                    schema_name = self.sanitize_schema_name(tenant_name)
                    
                    # Validate schema name
                    if schema_name == 'public':
                        return Response({
                            'error': 'Cannot use "public" as tenant name'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Check for existing tenant with same schema or domain
                    if Client.objects.filter(schema_name=schema_name).exists():
                        return Response({
                            'error': f'Tenant with schema name "{schema_name}" already exists'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    if Domain.objects.filter(domain=domain_name).exists():
                        return Response({
                            'error': f'Domain "{domain_name}" already exists'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create the tenant
                    tenant = Client.objects.create(
                        name=tenant_name,
                        schema_name=schema_name,
                        paid_until='2024-12-31',
                        on_trial=True
                    )
                    
                    # # Create the domain
                    domain = Domain.objects.create(
                        domain=domain_name,
                        tenant=tenant,
                        is_primary=True
                    )


            # Switch to the tenant's schema
            # with schema_context(schema_name):
            #     # Dynamically create the Customer table in the tenant's schema
            #     with connection.schema_editor() as schema_editor:
            #         schema_editor.create_model(Customer)

            return Response({
                'message': 'Tenant and Customer table created successfully',
                'tenant': {
                    'name': tenant.name,
                    'schema_name': tenant.schema_name
                },
                'domain': domain.domain
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def sanitize_schema_name(self, name):
        """
        Sanitize the schema name by:
        1. Converting to lowercase
        2. Replacing spaces with underscores
        3. Removing special characters
        """
        # Convert to lowercase and replace spaces
        sanitized = name.lower().replace(' ', '_')
        
        # Remove any characters that are not alphanumeric or underscore
        sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
        
        # Ensure the schema name is not empty
        return sanitized or 'tenant'

class AddCustomerDetails(APIView):
    def post(self, request):
        try:
            # Ensure we're in the public schema
            with schema_context('public'):
                with transaction.atomic():
                    tenant_id = request.data.get('tenant_id')
                    customer_id = request.data.get('customer_id')
                    client = Client.objects.filter(pk=tenant_id).first()

                    if not client:
                        return Response({
                            'error': f'No tenant found with ID {tenant_id}'
                        }, status=status.HTTP_404_NOT_FOUND)

                    # Extract schema_name
                    schema_name = client.schema_name

            # Switch to the tenant's schema
            with schema_context(schema_name):
                with transaction.atomic():
                    # Get other fields from the request
                    name = request.data.get('name')
                    account_name = request.data.get('account_name')
                    channels = request.data.get('channels')
                    tickets_count = request.data.get('tickets_count')

                    if not name or not account_name:
                        return Response({
                            'error': 'Both name and account_name are required'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Check if the customer already exists
                    if Customer.objects.filter(customer_id=customer_id).exists():
                        return Response({
                            'message': 'Merchant details already exist...'
                        }, status=status.HTTP_200_OK)

                    # Create the customer in the tenant's schema
                    customer = Customer.objects.create(
                        customer_id=customer_id,
                        merchant_id=client,  # Link to the client using the foreign key
                        name=name,
                        account_name=account_name,
                        channels=channels,
                        tickets_count=tickets_count
                    )

                    # Return success response
                    return Response({
                        'message': 'Customer created successfully',
                        'customer': {
                            'customer_id': str(customer.customer_id),
                            'name': customer.name,
                            'account_name': customer.account_name
                        }
                    }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class CustomerSeederView(APIView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()

    def post(self, request):
        """
        Seed customers in a specified schema.
        """
        try:
            # Extract parameters
            schema_name = request.data.get('schema_name')
            num_records = request.data.get('num_records', 10)
            tenant_id = request.data.get('tenant_id')

            # Validate inputs
            if not schema_name:
                return Response({
                    'error': 'Schema name is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify schema and get tenant
            with schema_context('public'):
                if tenant_id:
                    client = Client.objects.filter(pk=tenant_id, schema_name=schema_name).first()
                    if not client:
                        return Response({
                            'error': f'No tenant found with ID {tenant_id} and schema {schema_name}'
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    client = Client.objects.filter(schema_name=schema_name).first()
                    if not client:
                        return Response({
                            'error': f'No tenant found with schema {schema_name}'
                        }, status=status.HTTP_404_NOT_FOUND)

            # Seed data in the specified schema
            with schema_context(schema_name):
                with transaction.atomic():
                    created_customers = self.generate_customers(client, num_records)

                    return Response({
                        'message': f'Successfully created {num_records} customers',
                        'total_created': len(created_customers),
                        'customers': created_customers
                    }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_customers(self, client, num_records):
        """
        Generate and create customer records.
        """
        created_customers = []

        for _ in range(num_records):
            customer = self.create_customer(client)
            created_customers.append({
                'customer_id': customer.customer_id,
                'name': customer.name,
                'account_name': customer.account_name,
                'channels': customer.channels,
                'tickets_count': customer.tickets_count
            })

        return created_customers

    def create_customer(self, client):
        """
        Create a single customer with fake data.
        """
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()

        customer = Customer.objects.create(
            customer_id=str(uuid.uuid4()),  # Generate a unique ID
            merchant_id=client,
            name=f"{first_name} {last_name}",
            account_name=self.generate_account_name(first_name, last_name),
            channels=self.generate_channel(),
            tickets_count=self.generate_ticket_count(),
            is_deleted=False
        )

        return customer

    def generate_account_name(self, first_name, last_name):
        """
        Generate a unique account name.
        """
        account_name_formats = [
            f"{first_name.lower()}{last_name.lower()}_{self.fake.random_int(min=100, max=999)}",
            f"{first_name[0].lower()}{last_name.lower()}_{self.fake.random_int(min=1000, max=9999)}",
            f"{self.fake.user_name()}_{self.fake.random_int(min=10, max=99)}"
        ]
        return random.choice(account_name_formats)

    def generate_channel(self):
        """
        Generate a communication channel.
        """
        channels = ['instagram', 'facebook', 'twitter', 'whatsapp']
        return random.choice(channels)

    def generate_ticket_count(self):
        """
        Generate a realistic ticket count.
        """
        ticket_distributions = [
            lambda: random.randint(0, 3),  # Low volume
            lambda: random.randint(4, 10),  # Medium volume
            lambda: random.randint(11, 25),  # High volume
            lambda: random.randint(0, 1)  # Very low volume
        ]
        return random.choices(ticket_distributions, weights=[0.5, 0.3, 0.1, 0.1])[0]()
  
class CustomUserSeederView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()

    def post(self, request):
        """
        Seed users in the specified schema using Faker data.
        """
        # Number of users to create
        num_records = request.data.get('num_records', 5)
        schema_name = request.data.get('schema_name')

        if not schema_name:
            return Response({
                'error': 'schema_name is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Seed data in the specified schema
            with schema_context(schema_name):
                created_users = self.generate_users(num_records)

                return Response({
                    'message': f'Successfully created {num_records} users',
                    'total_created': len(created_users),
                    'users': created_users
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_users(self, num_records):
        """
        Generate and create user records in bulk using Faker.
        """
        created_users = []

        for _ in range(num_records):
            user_data = self.prepare_user_data()
            
            # Use serializer for validation and creation
            serializer = CustomUserSerializer(data=user_data)
            
            if serializer.is_valid():
                user = serializer.save()
                created_users.append(serializer.data)
            else:
                print(f"Validation Error: {serializer.errors}")

        return created_users

    def prepare_user_data(self):
        """
        Prepare realistic user data using Faker
        """
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        username = self.fake.user_name()


        # Generate a random password for each user
        password = self.fake.password()

        return {
            'email': self.fake.email(),
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'role': random.choice(['merchant', 'customer']),  # Random role
            'is_active': True,
            'is_staff': False,  # Set to False by default, or modify as needed
            'password': password,  # Ensure password is included

        }

class UpdateUserEmailView(APIView):

    def post(self, request):
        """
        Update the email of a CustomUser in a specific schema.
        """
        tenant_id = request.data.get('id')
        schema_name = request.data.get('schema_name')
        new_email = request.data.get('new_email')

        if not tenant_id or not schema_name or not new_email:
            return Response({
                'error': 'id, schema_name, and new_email are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Switch to the schema for the given tenant
            with schema_context(schema_name):
                # Find the user by tenant_id
                user = CustomUser.objects.get(id=tenant_id)
                
                # Update the email
                user.email = new_email
                user.save()

                return Response({
                    'message': f'Successfully updated email for user with tenant_id {tenant_id}',
                    'user': CustomUserSerializer(user).data
                }, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SendEmailAPIView(APIView):
    def post(self, request):
        try:
            tenant_id = request.data.get('tenant_id')
            schema_name = request.data.get('schema_name')
            id = request.data.get('id')

            if not tenant_id or not schema_name:
                return Response({
                    'error': 'Both tenant_id and schema_name are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if tenant exists in the public schema
            with schema_context('public'):
                client = Client.objects.filter(pk=tenant_id).first()

                if not client:
                    return Response({
                        'error': f'Tenant with ID {tenant_id} not found'
                    }, status=status.HTTP_404_NOT_FOUND)

            # Ensure the schema_name matches the tenant's schema_name
            if client.schema_name != schema_name:
                return Response({
                    'error': 'Provided schema_name does not match the tenant'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Switch to the tenant's schema to fetch the email
            with schema_context(schema_name):
                user_email = CustomUser.objects.filter(pk=id).values_list('email', flat=True).first()

                if not user_email:
                    return Response({
                        'error': 'No email found in CustomUser table'
                    }, status=status.HTTP_404_NOT_FOUND)

            # Prepare email details
            subject = "Testing Email"
            body = "This is a test email."

            # Send email asynchronously using Celery
            send_async_email2("Test Subject", user_email, "Test Body")

            return Response({
                'message': 'Email is being sent!',
                'recipient_email': user_email
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# following function is for seeeding data to Merchant-->Ticket table
class TicketSeederView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()

    def set_schema(self, schema_name):
        """
        Set the schema for database operations.
        """
        connections['default'].set_schema(schema_name)

    def post(self, request):
        """
        Seed ticket data in the specified schema using Faker data.
        """
        # Number of tickets to create
        num_records = request.data.get('num_records', 5)
        schema_name = request.data.get('schema_name')
        tenant_id = request.data.get('tenant_id')

        if not schema_name or not tenant_id:
            return Response({
                'error': 'schema_name and tenant_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Set the schema context for the operation
            self.set_schema(schema_name)

            # Fetch the first customer ID for the schema
            customer_id = Customer.objects.values_list('customer_id', flat=True).first()
            print("customer",customer_id)

            if not customer_id:
                return Response({
                    'error': 'No customers found in the specified schema'
                }, status=status.HTTP_404_NOT_FOUND)

            # Generate tickets
            created_tickets = self.generate_tickets(num_records, customer_id, tenant_id)

            return Response({
                'message': f'Successfully created {num_records} tickets',
                'total_created': len(created_tickets),
                'tickets': created_tickets
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_tickets(self, num_records, customer_id, tenant_id):
        """
        Generate and create ticket records in bulk using Faker.
        """
        created_tickets = []

        for _ in range(num_records):
            ticket_data = self.prepare_ticket_data(customer_id, tenant_id)

            # Use serializer for validation and creation
            serializer = TicketSerializer(data=ticket_data)

            if serializer.is_valid():
                ticket = serializer.save()
                created_tickets.append(serializer.data)
            else:
                print(f"Validation Error: {serializer.errors}")

        return created_tickets

    def prepare_ticket_data(self, customer_id, tenant_id):
        """
        Prepare realistic ticket data using Faker
        """
        subject = self.fake.sentence(nb_words=6)
        priority = random.choice(['1', '2'])  # Low or High priority
        channel = random.choice(['Twitter', 'Instagram', 'Email', 'WhatsApp'])
        status = random.choice(['open', 'deferred', 'closed'])

        return {
            'customer_id': str(customer_id),  # First customer ID from the schema
            'merchant_id': str(tenant_id),   # Automatically assigned from tenant_id
            'subject': subject,
            'priority': priority,
            'channel': channel,
            'status': status,
            'response_recap': self.fake.text(),
            'deferred_at': None,
            'closed_reason': None,
        }


class ChannelSeederView(APIView):
    """
    A view to seed channels for a given schema and tenant.
    """

    fake = Faker()

    def prepare_channel_data(self, customer_id, tenant_id):
        """
        Prepare realistic channel data using Faker.
        """
        name = random.choice(['Twitter', 'Instagram', 'Email', 'WhatsApp'])
        account_name = self.fake.user_name()
        account_password = self.fake.password()

        return {
            'customer_id': str(customer_id),  # First customer ID from the schema
            'merchant_id': str(tenant_id),    # Automatically assigned from tenant_id
            'name': name,
            'account_name': account_name,
            'account_password': account_password,
            'channel_active_status': True,
        }

    def generate_channels(self, num_records, customer_id, tenant_id):
        """
        Generate and create channel records in bulk using Faker.
        """
        created_channels = []

        for _ in range(num_records):
            channel_data = self.prepare_channel_data(customer_id, tenant_id)

            # Use serializer for validation and creation
            serializer = ChannelSerializer(data=channel_data)

            if serializer.is_valid():
                channel = serializer.save()
                created_channels.append(serializer.data)
            else:
                print(f"Validation Error: {serializer.errors}")
                print(f"Invalid Data: {channel_data}")

        return created_channels

    def post(self, request):
        """
        Handle POST request to seed channels for the given schema name and tenant ID.
        """
        schema_name = request.data.get('schema_name')
        tenant_id = request.data.get('tenant_id')
        num_records = request.data.get('num_records', 10)

        if not schema_name or not tenant_id:
            return Response({
                "error": "schema_name and tenant_id are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the schema exists
        with schema_context(schema_name):
            # Fetch the first customer ID for the given schema
            customer = Customer.objects.first()

            if not customer:
                return Response({
                    "message": "No customers found in the schema.",
                    "total_created": 0,
                    "channels": []
                }, status=status.HTTP_404_NOT_FOUND)

            customer_id = customer.customer_id  # First customer's ID

            # Generate channels
            created_channels = self.generate_channels(num_records, customer_id, tenant_id)

            return Response({
                "message": f"Successfully created {len(created_channels)} channels",
                "total_created": len(created_channels),
                "channels": created_channels
            }, status=status.HTTP_201_CREATED if created_channels else status.HTTP_400_BAD_REQUEST)



class SeedKnowledgeBaseView(APIView):
    """
    A view to seed knowledge bases for a given schema and tenant.
    """

    fake = Faker()

    def prepare_knowledge_base_data(self, customer_id, tenant_id):
        """
        Prepare realistic knowledge base data using Faker.
        """
        name = self.fake.word()
        version = random.randint(1, 5)
        file_path = self.fake.file_path()

        return {
            'customer_id': str(customer_id),  # First customer ID from the schema
            'merchant_id': str(tenant_id),    # Automatically assigned from tenant_id
            'name': name,
            'version': version,
            'file_path': file_path,
            'is_deleted': False,
        }

    def generate_knowledge_bases(self, num_records, customer_id, tenant_id):
        """
        Generate and create knowledge base records in bulk using Faker.
        """
        created_kbs = []

        for _ in range(num_records):
            kb_data = self.prepare_knowledge_base_data(customer_id, tenant_id)

            # Use serializer for validation and creation
            serializer = KnowledgeBaseSerializer(data=kb_data)

            if serializer.is_valid():
                kb = serializer.save()
                created_kbs.append(serializer.data)
            else:
                print(f"Validation Error: {serializer.errors}")
                print(f"Invalid Data: {kb_data}")

        return created_kbs

    def post(self, request):
        """
        Handle POST request to seed knowledge bases for the given schema name and tenant ID.
        """
        schema_name = request.data.get('schema_name')
        tenant_id = request.data.get('tenant_id')
        num_records = request.data.get('num_records', 10)

        if not schema_name or not tenant_id:
            return Response({
                "error": "schema_name and tenant_id are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the schema exists
        with schema_context(schema_name):
            # Fetch the first customer ID for the given schema
            customer = Customer.objects.first()

            if not customer:
                return Response({
                    "message": "No customers found in the schema.",
                    "total_created": 0,
                    "knowledge_bases": []
                }, status=status.HTTP_404_NOT_FOUND)

            customer_id = customer.customer_id  # First customer's ID

            # Generate knowledge bases
            created_kbs = self.generate_knowledge_bases(num_records, customer_id, tenant_id)

            return Response({
                "message": f"Successfully created {len(created_kbs)} knowledge bases",
                "total_created": len(created_kbs),
                "knowledge_bases": created_kbs
            }, status=status.HTTP_201_CREATED if created_kbs else status.HTTP_400_BAD_REQUEST)
