from django.contrib import admin
from .models import *
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
    queryset.update(is_approved=True)


class SkuPostAdmin(admin.ModelAdmin):
    list_display = ('sku', 'user_id', 'text', 'location', 'creationDate', 'is_approved')
    list_filter = ('is_approved', 'creationDate')
    search_fields = ('sku__sku', 'user_id__username', 'text')
    actions = (approve_comments,)


class LikePostAdmin(admin.ModelAdmin):
    list_display = ('skuPost', 'user_id', 'creationDate')
    search_fields = ('skuPost__sku__sku', 'user_id__username')

admin.site.register(Item, ItemAdmin)
admin.site.register(Consumer, ConsumerAdmin)
admin.site.register(Scan, ScanAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(skuPost, SkuPostAdmin)
admin.site.register(likePost, LikePostAdmin)
