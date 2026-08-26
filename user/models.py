from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    countries = [
        ('CO', 'Colombia'),
        ('CR', 'Costa Rica'),
        ('DO', 'Rep. Dominicana'),
        ('GT', 'Guatemala'),
        ('HN', 'Honduras'),
        ('JM', 'Jamaica'),
        ('NI', 'Nicaragua'),
        ('PA', 'Panama'),
        ('SV', 'El Salvador'),
        ('US', 'United States'),
        ('UY', 'Uruguay'),
        ('VE', 'Venezuela'),
        ('Otro', 'Otro')
    ]
    location = models.CharField(max_length=100, choices=countries, blank=True)
    email = User.username
    telephone = models.CharField(max_length=50, blank=True, default="")
    movil = models.CharField(max_length=50, blank=True, default="")
    direccion = models.CharField(max_length=100, blank=True, default="")
    member_since = models.DateTimeField(auto_now_add=True)
    ig_link = models.URLField(max_length=500, blank=True, null=True)
    fb_link = models.URLField(max_length=500, blank=True, null=True)
    tw_link = models.URLField(max_length=500, blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, default='')




    def __str__(self):
        return self.user.username
