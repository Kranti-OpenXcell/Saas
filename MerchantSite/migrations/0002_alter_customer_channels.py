# Generated by Django 5.1.4 on 2024-12-10 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MerchantSite', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='channels',
            field=models.CharField(max_length=50),
        ),
    ]
