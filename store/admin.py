from django.contrib import admin 
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=['id','name','status','created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=['id','name','status',]
@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    pass
@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'size','original_price', 'offer')
    list_editable = ('offer',)

@admin.register(ProductImages)
class ProductImagesAdmin(admin.ModelAdmin):
    pass

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display=['title']

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display=['city','pincode','district','state']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "user__email", "id")
    


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")
    list_filter = ("product",)    

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_amount", "active", "valid_from", "valid_to")
    search_fields = ("code",)
    list_filter = ("active",)
