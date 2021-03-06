# Generated by Django 3.2.5 on 2021-08-02 19:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(max_length=200)),
                ('name', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Scan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('where', models.CharField(default='', max_length=100)),
                ('when', models.CharField(default='', max_length=100)),
                ('country', models.CharField(default='', max_length=100)),
                ('city', models.CharField(default='', max_length=100)),
                ('sku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='britishdenim.item')),
            ],
        ),
        migrations.CreateModel(
            name='Consumer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('where', models.CharField(default='', max_length=100)),
                ('when', models.CharField(default='', max_length=100)),
                ('country', models.CharField(default='', max_length=100)),
                ('city', models.CharField(default='', max_length=100)),
                ('getInfo', models.BooleanField(default=True)),
                ('sku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='britishdenim.item')),
                ('user_id', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
