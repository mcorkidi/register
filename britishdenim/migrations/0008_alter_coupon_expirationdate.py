# Generated by Django 4.0.1 on 2023-05-22 16:24

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('britishdenim', '0007_alter_coupon_expirationdate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='expirationDate',
            field=models.DateTimeField(default=datetime.datetime(2023, 5, 22, 16, 24, 47, 439737, tzinfo=utc)),
        ),
    ]
