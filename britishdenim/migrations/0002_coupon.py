# Generated by Django 3.2.5 on 2021-08-26 02:48

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('britishdenim', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creationDate', models.DateTimeField(auto_now_add=True)),
                ('expirationDate', models.DateTimeField(default=datetime.date(2021, 9, 25))),
                ('details', models.TextField(default='')),
                ('image', models.ImageField(default='coupon.jpg', upload_to='coupon_images')),
                ('issuer', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]