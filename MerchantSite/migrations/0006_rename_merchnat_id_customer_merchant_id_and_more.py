# Generated by Django 5.1.4 on 2024-12-12 05:43

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Merchant', '0001_initial'),
        ('MerchantSite', '0005_knowledgebase_ticket'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customer',
            old_name='merchnat_id',
            new_name='merchant_id',
        ),
        migrations.AlterField(
            model_name='ticket',
            name='customer_id',
            field=models.UUIDField(),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='merchant_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets_related', to='Merchant.client'),
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('channel_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(choices=[('Twitter', 'Twitter'), ('Instagram', 'Instagram'), ('Email', 'Email'), ('WhatsApp', 'WhatsApp')], max_length=10)),
                ('account_name', models.CharField(max_length=255)),
                ('account_password', models.CharField(max_length=255)),
                ('channel_active_status', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_channels', to='MerchantSite.customer')),
                ('merchant_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels_related', to='Merchant.client')),
            ],
        ),
    ]
