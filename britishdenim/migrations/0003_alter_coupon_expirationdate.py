# Generated by Django 3.2.5 on 2021-08-26 03:00

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('britishdenim', '0002_coupon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='expirationDate',
            field=models.DateTimeField(default=datetime.datetime(2021, 8, 26, 3, 0, 25, 696023, tzinfo=utc)),
        ),
    ]