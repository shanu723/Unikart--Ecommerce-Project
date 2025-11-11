from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone
import uuid, os
from PIL import Image,ImageOps
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta




class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    


class Category(models.Model):
    name = models.CharField(max_length=100)
    status=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    offer=models.ForeignKey('Offer',on_delete=models.SET_NULL,blank=True,null=True,related_name='products_with_this_category')
    def __str__(self):
        return self.name

class UserProfile(models.Model): 
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile') 
    is_blocked=models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    def __str__(self): 
        return self.user.username

@receiver(post_save,sender=User)
def create_user_profile(sender,instance,created,**kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)  


class Address(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='address')
    street= models.CharField(max_length=100,blank=True,null=True)
    city=models.CharField(max_length=100,blank=True,null=True)
    district=models.CharField(max_length=100,blank=True,null=True) 
    state=models.CharField(max_length=100,blank=True,null=True)
    pincode=models.CharField(max_length=6,blank=True,null=True)
    
    is_default=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.city}"

class Product(models.Model):
    name=models.CharField(max_length=100,blank=False,null=False)
    brand=models.CharField(max_length=100,blank=True,null=True)
    
    category=models.ForeignKey(Category,on_delete=models.CASCADE,null=True,blank=True)
    offer=models.ForeignKey('Offer',on_delete=models.CASCADE,null=True,blank=True,related_name='products_with_this_offer')
    created_at=models.DateTimeField(auto_now_add=True)
    status=models.BooleanField(null=False,default=False)
    description=models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

class Variation(models.Model):
    SIZE_CHOICES=[
        ('32','32 inch'),
        ('43','43 inch'),
        ('50','50 inch'),
        ('60','60 inch')
    ]
    size=models.CharField(max_length=10,choices=SIZE_CHOICES)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)    
    
    original_price=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0.01)])
    stock=models.PositiveIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    status=models.BooleanField(null=False, default=True)
    offer=models.ForeignKey('Offer',on_delete=models.SET_NULL,blank=True,null=True)
    def is_in_stock(self):
        return self.stock > 0
    def __str__(self):
        return f"{self.product.name}-{self.original_price}-{self.size}"

    
class Highlight(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='highlights')
    key = models.CharField(max_length=50)    # e.g., "RAM", "Display Size"
    value = models.CharField(max_length=200) # e.g., "4GB", "55 inches"

    def __str__(self):
        return f"{self.key}: {self.value}"



def getfilename(instance,filename):
    ext=filename.split('.')[-1] 
    filename=f"{uuid.uuid4()}.{ext}"
    return os.path.join('images',filename)       

class ProductImages(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='productimages')
    product_image = models.ImageField(upload_to=getfilename, validators=[FileExtensionValidator(allowed_extensions=['jpg','png','webp','jpeg'])])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)    
        try:
            img = Image.open(self.product_image.path)
            max_size = (800,800)
            
            img = ImageOps.fit(img,max_size,images.LANCZOS)
            img.save(self.product_image.path)
            
        except Exception as e:
            print(f"Image resize failed:{e}")      # Just log the error

    def __str__(self):
        return f"{self.product.name} - Image"


class Offer(models.Model):
    title=models.CharField(max_length=100,null=True,blank=True)
    DISCOUNT_CHOICES=(
        ('percentage','Percentage'),
        ('flat','Flat')
    )
    discount_type=models.CharField(max_length=20,choices=DISCOUNT_CHOICES)
    dis_value=models.PositiveIntegerField()
    is_active=models.BooleanField(default=True)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    OFFER_TYPES=(
        ('category','Category'),
        ('product','Product')
    )
    offer_type=models.CharField(max_length=30,choices=OFFER_TYPES)
    category=models.ForeignKey(Category,on_delete=models.CASCADE,null=True,blank=True,related_name='offer_on_this_category')
    product=models.ForeignKey(Product,on_delete=models.CASCADE,null=True,blank=True,related_name='offers_on_this_product')
    def __str__(self):
        return self.title or f"Offer {self.id}"

    def is_valid(self):
        now=timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_to

class Order(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Processing", "Processing"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    address=models.ForeignKey(Address,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Pending")


    subtotal = models.DecimalField(max_digits=10, decimal_places = 2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places =2,default=0)
    shipping = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    total = models.DecimalField(max_digits=10,decimal_places=2,default=2)
    payment_method = models.CharField(max_length=50,blank=True,null=True)
    def __str__(self):
        return f"Order{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order=models.ForeignKey(Order,related_name='items',on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    price=models.DecimalField(max_digits=10,decimal_places=2)

    def __str__(self):
        return f"{self.quantity}*{self.product.name}"

class ReturnRequest(models.Model):
    STATUS_CHOICES=[
        ('Pending','Pending'),
        ('Accepted','Accepted'),
        ('Rejected','Rejected'),
    ]      
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='Pending')
    created_at = models.DateTimeField(default=timezone.now) 

    def __str__(self):
        return f"REturn Request for Order #{self.order.id}({self.status})"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=20, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2,default=0)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"        

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code        

class Wallet(models.Model):
    user =models.OneToOneField(User,on_delete=models.CASCADE,related_name='wallet')
    balance = models.DecimalField(max_digits=10,decimal_places=3,default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

    def add_money(self,amount):
        self.balance += amount
        self.save()

    def deduct_money(self,amount):
        if self.balance>=amount:
            self.balance-=amount
            self.save()
            return True
        return False           

class Wishlist(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"