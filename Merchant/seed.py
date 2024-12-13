from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context
from Merchant.models import Client
from MerchantSite.models import Customer
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Seed data into a tenant schema'

    def add_arguments(self, parser):
        parser.add_argument('--schema', type=str, help='Specify the schema name to seed data into')
        parser.add_argument('--number', type=int, default=10, help='Number of records to create')

    def handle(self, *app_labels, **options):
        if not app_labels:
            raise CommandError('At least one app_label is required. Specify the app containing the models to seed data into.')

        app_label = app_labels[0]
        schema_name = options['schema']
        number = options['number']

        if not schema_name:
            raise CommandError('Schema name is required. Use --schema=<schema_name>')

        try:
            # Ensure the schema exists
            client = Client.objects.filter(schema_name=schema_name).first()
            if not client:
                raise CommandError(f'Schema "{schema_name}" does not exist.')

            fake = Faker()

            # Seed data in the specified schema
            with schema_context(schema_name):
                for _ in range(number):
                    Customer.objects.create(
                        merchnat_id=client,
                        name=fake.name(),
                        account_name=fake.company(),
                        channels=random.choice(['Email', 'Chat', 'Phone']),
                        tickets_count=random.randint(1, 100)
                    )

            self.stdout.write(self.style.SUCCESS(f'Successfully seeded {number} records into schema "{schema_name}" for app "{app_label}"'))

        except Exception as e:
            raise CommandError(f'An error occurred: {str(e)}')