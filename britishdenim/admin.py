from django.contrib import admin
from .models import *
from .email_utils import send_post_approval_email
# Register your models here.

class ItemAdmin(admin.ModelAdmin):

    list_display = ('sku', 'name', 'creationDate')
    search_fields = ['sku']


class ConsumerAdmin(admin.ModelAdmin):

    list_display = ('sku', 'user_id', 'where', 'when', 'country', 'city')

class ScanAdmin(admin.ModelAdmin):

    list_display = ('sku', 'where', 'when', 'country', 'city')

class CouponAdmin(admin.ModelAdmin):
    list_display = ('issuer', 'creationDate', 'expirationDate')


@admin.action(description='Approve selected comments')
def approve_comments(modeladmin, request, queryset):
    posts = list(queryset.filter(is_approved=False).select_related('sku', 'user_id'))
    queryset.filter(pk__in=[post.pk for post in posts]).update(is_approved=True)
    for post in posts:
        post.is_approved = True
        if send_post_approval_email(request, post):
            skuPost.objects.filter(pk=post.pk).update(approval_email_sent=True)


class SkuPostAdmin(admin.ModelAdmin):
    list_display = ('sku', 'user_id', 'text', 'location', 'creationDate', 'is_approved', 'approval_email_sent')
    list_filter = ('is_approved', 'creationDate')
    search_fields = ('sku__sku', 'user_id__username', 'text')
    actions = (approve_comments,)

    def save_model(self, request, obj, form, change):
        was_approved = change and skuPost.objects.filter(pk=obj.pk, is_approved=True).exists()
        super().save_model(request, obj, form, change)
        if obj.is_approved and not was_approved and not obj.approval_email_sent:
            if send_post_approval_email(request, obj):
                obj.approval_email_sent = True
                obj.save(update_fields=['approval_email_sent'])


class LikePostAdmin(admin.ModelAdmin):
    list_display = ('skuPost', 'user_id', 'creationDate')
    search_fields = ('skuPost__sku__sku', 'user_id__username')

admin.site.register(Item, ItemAdmin)
admin.site.register(Consumer, ConsumerAdmin)
admin.site.register(Scan, ScanAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(skuPost, SkuPostAdmin)
admin.site.register(likePost, LikePostAdmin)
