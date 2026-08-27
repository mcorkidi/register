from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



# Create your models here.

class Item(models.Model):
    sku = models.CharField(max_length=200)
    name = models.CharField(max_length=200, default="")
    creationDate = models.DateTimeField(auto_now_add=True)

        # def __str__(self):
        #     return self.sku

class skuPost(models.Model):
    sku = models.ForeignKey(Item, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    text = models.TextField(max_length=280, blank=True)
    location = models.CharField(max_length=100, blank=True)
    creationDate = models.DateTimeField(auto_now_add=True)
    imageList = models.CharField(max_length=500, blank=True)
    is_approved = models.BooleanField(default=False)
    approval_email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-creationDate']

    def __str__(self):
        return f'{self.sku.sku} comment by {self.user_id}'

class likePost(models.Model):
    skuPost=models.ForeignKey(skuPost, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    creationDate = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('skuPost', 'user_id'),
                name='unique_user_like_per_sku_post',
            ),
        ]


class Consumer(models.Model):

    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    sku = models.ForeignKey(Item,on_delete=models.CASCADE)
    where = models.CharField(max_length=100, default="")
    when = models.CharField(max_length=100, default="")
    country = models.CharField(max_length=100, default="")
    city = models.CharField(max_length=100, default="")
    getInfo = models.BooleanField(default = True)
    post_invitation_sent_at = models.DateTimeField(blank=True, null=True)

    # def __str__(self):
    #     return self.sku


class PostInviteCampaign(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_email_at = models.DateTimeField(blank=True, null=True)


class PostInviteCampaignItem(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        SKIPPED_SENT = 'skipped_sent', 'Skipped: already invited'
        SKIPPED_APPROVED = 'skipped_approved', 'Skipped: post approved'
        SKIPPED_NO_EMAIL = 'skipped_no_email', 'Skipped: no email'
        FAILED = 'failed', 'Failed'

    campaign = models.ForeignKey(PostInviteCampaign, on_delete=models.CASCADE, related_name='items')
    registration = models.ForeignKey(Consumer, on_delete=models.CASCADE)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('campaign', 'registration'),
                name='unique_campaign_registration',
            ),
        ]
    
class Scan(models.Model):
    sku = models.ForeignKey(Item,on_delete=models.CASCADE)
    where = models.CharField(max_length=100, default="")
    when = models.CharField(max_length=100, default="")
    country = models.CharField(max_length=100, default="")
    city = models.CharField(max_length=100, default="")

    def __str__(self):
        return str(self.sku)
    
class Coupon(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    issuer = models.CharField(max_length=100, default="")
    city = models.CharField(max_length=100, default='')
    country = models.CharField(max_length=100, default='')
    creationDate = models.DateTimeField(auto_now_add=True)
    expirationDate = models.DateTimeField(default= timezone.now)
    details = models.TextField(default="")
    image = models.ImageField(default='coupon.jpg', upload_to='coupon_images')
    industry = models.CharField(max_length=100, default='')
    link = models.URLField(default='')
    

      
