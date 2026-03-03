from django import forms
from django.core.exceptions import ValidationError
from .models import Coupon
import re


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