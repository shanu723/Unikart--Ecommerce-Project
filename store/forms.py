from django import forms
from django.core.exceptions import ValidationError
from .models import Coupon,Offer
import re
class OfferForm(forms.ModelForm):
    class Meta:
       model=Offer
       fields='__all__'

    def clean(self):
        cleaned_data = super().clean()
        offer_type = cleaned_data.get('offer_type')
        product = cleaned_data.get('product')
        category = cleaned_data.get('category')
        discount_type= cleaned_data.get('discount_type')
        dis_value = cleaned_data.get('dis_value')
        valid_from = cleaned_data.get('valid_from')   
        valid_to = cleaned_data.get('valid_to')

        if offer_type == 'category' and not category:
            raise ValidationError("Please select a category for category offer")
        if offer_type == 'product' and not product:
            raise ValidationError("Please select a product for product offer")
        if dis_value<=0:
            raise ValidationError("Discount must be greater than 0")
        if discount_type == 'percentage' and dis_value >80:
            raise ValidationError("Maximum allowed discount is 80%")
        if discount_type == 'flat' and product and dis_value >= variation.original_price:
            raise ValidationError("Flat discount can't be exceet product price")
        if valid_from and valid_to and valid_from>= valid_to:
            raise ValidationError("Valid must be before valid To")

        overlapping_offers = Offer.objects.filter(offer_type=offer_type,is_active=True) 
        if offer_type == 'category' and category:
            overlapping_offers = overlapping_offers.filter(category=category)
        elif offer_type == 'product' and product:
            overlapping_offers = overlapping_offers.filter(product=product)
        overlapping_offers= overlapping_offers.filter(
            valid_from__lt=valid_to,
            valid_to__gt=valid_from
        )    
        if self.instance.pk:
            overlapping_offers= overlapping_offers.exclude(pk=self.instance.pk)
        if overlapping_offers.exists():
            raise ValidationError("An active offer already exists for this prodcut")
        return cleaned_data        



class CouponForm(forms.ModelForm):

    class Meta:
        model = Coupon
        fields = '__all__'
        widgets = {
            
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'min_purchase_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    def clean_code(self):
        code = self.cleaned_data.get('code')

        if not code:
            raise ValidationError("Coupon code is required")

        code = (self.cleaned_data.get('code') or "").strip().upper()

        if not code:
            raise ValidationError("Coupon code cannot be empty")

        
        if not re.match(r'^(?=.*[A-Za-z0-9])[A-Za-z0-9_-]+$', code):
            raise ValidationError(
                "Coupon code can only contain letters, numbers, '-' and '_'"
            )

        return code.upper()
    def clean_discount_value(self):
        discount_type = self.cleaned_data.get('discount_type')
        discount_value = self.cleaned_data.get('discount_value')

        if discount_value is None:
            raise ValidationError("Discount value is required")

        if discount_value <= 0:
            raise ValidationError("Discount must be greater than 0")

        if discount_type == "percentage" and discount_value > 100:
            raise ValidationError("Percentage cannot be more than 100")

        return discount_value


    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")

        if valid_from and valid_to and valid_to < valid_from:
            raise ValidationError("Valid To cannot be before Valid From")

        return cleaned_data