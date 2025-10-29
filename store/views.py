import random
import razorpay
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils import timezone
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import authenticate, login,logout
from django.db import transaction
from django.db.models import Min,Max
from django.contrib import messages
from datetime import timedelta
from .models import Product, Variation, Highlight, ProductImages,UserOTP,Category,Offer,UserProfile,Address,Order,CartItem,Order,Wallet,Wishlist,Coupon,OrderItem
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import json
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from .forms import OfferForm
from store.utils import get_best_price

# Create your views here.
def home(request):
    return render(request,'index.html') 
 
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
          
            if user.is_superuser:
                login(request, user)
                messages.success(request, "Logged in as admin.")
                return redirect('admin_dashboard') 

            
            if user.profile.is_blocked:
                messages.error(request, "Your account is blocked.")
                return redirect('login')

            
            login(request, user)
            
            messages.success(request, "Successfully logged in.")
            return redirect('user_dashboard')  
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')
    else:
        return render(request, 'login.html')

def login_error(request):
    return render(requst,'user/login_error.html')        
@login_required
def user_dashboard(request):
    return render(request, 'user/user_dashboard.html',{'user':request.user})         

def signup_view(request):
    if request.method=='POST':
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']

        if password!=confirm_password:
            messages.error(request,'Passwords does not match')
            return redirect('signup')
        if User.objects.filter(username=username).exists():
            messages.error(request,"Username already exists")    
            return redirect('signup')
        if User.objects.filter(email=email).exists():
            messages.error(request,'Email already exists')
            return redirect('signup')

        request.session['signup_data']={
            'username':username,
            'password':password,
            'email':email,   
        }
        code=f"{random.randint(100000,999999)}"
        request.session['signup_otp']=code
        request.session['signup_otp_time']=str(timezone.now())

        send_mail(
            subject='Verfication mail',
            message=f"Hai{username} This is your OTP{code}. iwll expires in 10 minutes",
            from_email="no-repaly@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request,"OTP sent successfully")
        return redirect('verify_otp',username=username)
    return render(request,'signup.html')  


def verify_otp(request,username):
    signup_data=request.session.get('signup_data')
    signup_otp=request.session.get('signup_otp')
    otp_time=request.session.get('signup_otp_time')

    if signup_data['username']!=username:
        messages.error(request,'session expired')
        return redirect('signup')

    if request.method=='POST':
        entered_otp=request.POST.get('otp')

        if entered_otp==signup_otp:
            otp_time=timezone.datetime.fromisoformat(otp_time)
        
            if timezone.now() - otp_time > timedelta(minutes=10):
                request.session.flush()
                messages.error(request,'otp expried.try again')
                return redirect('signup')

            
            user = User.objects.create_user(
                username=signup_data['username'],
                password=signup_data['password'],
                email=signup_data['email']
            )
            user.is_active = True
            user.save()

            profile, created = User_profile.objects.get_or_create(user=user)

            
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)  

            # Clearing otp keys
            for key in ['signup_data', 'signup_otp', 'signup_otp_time']:
                if key in request.session:
                    del request.session[key]

            messages.success(request,'Account verified.')
            return redirect('/profile/')
        else:
            message.error(request,'Invalid otp')
            return redner(request,'login.html')    


def user_list(request):
    filter_status = request.GET.get('status','all')

    if filter_status == 'blocked':
        users = User.objects.filter(profile__is_blocked = True)

    else:
        users = User.objects.all()

    return render(request,'admin_templates/user_list.html',{
        'users':users,
        'filter_status':filter_status
    })          


def block_user(request,user_id):
    userprofile = get_object_or_404(UserProfile, user__id=user_id)
    userprofile.is_blocked=True
    userprofile.save()
    messages.success(request,'User blocked successfully')
    return redirect('user_list')

def unblock_user(request,user_id):
    userprofile = get_object_or_404(UserProfile, user__id=user_id)
    userprofile.is_blocked=False
    userprofile.save()
    messages.success(request,'User is Unblocked successfully')
    return redirect('user_list')




@login_required
@user_passes_test(lambda u:u.is_superuser)
def admin_dashboard(request):
    return render(request,'admin_templates/admin_dashboard.html')

def category_list(request):
    categories=Category.objects.filter(status=True)
    return render(request,'admin_templates/category.html',{'categories':categories})
def add_category(request):
    if request.method=='POST':
        name=request.POST.get('name')
        status=request.POST.get('status')=='on'

        if Category.objects.filter(name__iexact=name):
            messages.error(request,"Category Already exists")
            return redirect('admin_templates/add_category')

        else:
            Category.objects.create(name=name,status=status)
            messages.success(request,"Category added successfully")
            return redirect('category')

    return render(request,'admin_templates/add_category.html')      

def edit_category(request,category_id):
    category=get_object_or_404(Category,id=category_id)
    if request.method=="POST":
        name=request.POST.get('name')
        status=request.POST.get('status')=='on'

        if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
            messages.error(request,'Category name exists')
            return redirect('edit_category',category_id=category_id)
        
        category.name=name
        category.status=status
        category.save()
        messages.success(request,"Category updated successfully")
        return redirect('category')
    return render(request,'admin_templates/edit_category.html',{'category':category})    

def delete_category(request,category_id):
    category=get_object_or_404(Category,id=category_id)
    category.status=False
    category.save()
    messages.success(request,"Category deleted successfully")
    return redirect('category')



@transaction.atomic
def product_list(request): 
    products = Product.objects.all().order_by('-id')

    search_product = request.GET.get('q','')
    if search_product:
        products = products.filter(name__icontains=search_product)
    paginator=Paginator(products,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    is_paginated = True
    return render(request, 'admin_templates/products.html', {'products': products,
    'page_obj':page_obj,
    'is_paginated':is_paginated})




def add_product(request):
    
    categories = Category.objects.all()
    if request.method == 'POST':
        try:
            product_name = request.POST.get('name')
            brand = request.POST.get('brand')
            description = request.POST.get('description')
            status = request.POST.get('status') == 'on'
            category_id = request.POST.get('category')
            stock_list = request.POST.getlist('stock[]')
            
            category = Category.objects.get(id=category_id)


            product = Product.objects.create(
                name=product_name,
                brand=brand,
                description=description,
                status=status,
                
                category=category
            )

        
            size = request.POST.getlist('size[]')
            original_price = request.POST.getlist('original_price[]')
            
            variation_status = request.POST.getlist('variation_status[]')

            for i in range(len(size)):
                is_active = variation_status[i] == 'on' if i < len(variation_status) else False
                Variation.objects.create(
                    product=product,
                    size=size[i],
                    original_price=original_price[i],
                    
                    stock=int(stock_list[i]) if i < len(stock_list) else 0,
                    status=is_active
                )

        
            keys = request.POST.getlist('highlight_keys[]')
            values = request.POST.getlist('highlight_values[]')

            for k, v in zip(keys, values):
                if k.strip() and v.strip():
                    Highlight.objects.create(product=product, key=k.strip(), value=v.strip())

                       
            for image in request.FILES.getlist('product_images'):
                ProductImages.objects.create(product=product, product_image=image)

            messages.success(request, 'Product added successfully!')
            return redirect('admin_dashboard')

        except Exception as e:
            print(e)
            messages.error(request, f"Something went wrong: {e}")
            return redirect('add_product')

    return render(request, 'admin_templates/add_product.html', {'categories': categories})


def edit_product(request,product_id):
    product=get_object_or_404(Product,id=product_id)
    categories=Category.objects.all()

    if request.method =='POST':
        try:
            product.name=request.POST.get('name')
            product.brand=request.POST.get('brand')
            product.description=request.POST.get('description')
            product.status=request.POST.get('status')=='on'
            category_id=request.POST.get('category')
            product.category=Category.objects.get(id=category_id)
            product.save()


            size_list=request.POST.getlist('size[]')
            price_list=request.POST.getlist('original_price[]')
            stock_list = request.POST.getlist('stock[]')
            variation_status = request.POST.getlist('variation_status[]')

            product.variation_set.all().delete()

            for i in range(len(size_list)):
                is_active = variation_status[i] == 'on' if i < len(variation_status) else False
                Variation.objects.create(
                    product=product,
                    size=size_list[i],
                    original_price=price_list[i],
                    stock=int(stock_list[i]) if i < len(stock_list) else 0,
                    status=is_active
                )

            
            product.highlights.all().delete()
            keys = request.POST.getlist('highlight_keys[]')
            values = request.POST.getlist('highlight_values[]')
            for k, v in zip(keys, values):
                if k.strip() and v.strip():
                    Highlight.objects.create(product=product, key=k.strip(), value=v.strip())

            if request.FILES.getlist('product_images'):
                product.productimages.all().delete()
                for image in request.FILES.getlist('product_images'):
                    ProductImages.objects.create(product=product, product_image=image)

            messages.success(request, 'Product updated successfully!')
            return redirect('admin_dashboard')

        except Exception as e:
            print(e)
            messages.error(request, f"Something went wrong: {e}")
            return redirect('edit_product', product_id=product.id)

    # GET request: populate the form with existing data
    variations = product.variation_set.all()
    highlights = product.highlights.all()
    images = product.productimages.all()

    context = {
        'product': product,
        'categories': categories,
        'variations': variations,
        'highlights': highlights,
        'images': images,
    }
    return render(request, 'admin_templates/edit_product.html', context)

@never_cache
def shop(request):
    is_authenticated = request.user.is_authenticated
    sort= request.GET.get('sort','newest')

    products = Product.objects.filter(status=True)
    if sort == 'low_to_high':
        products =products.annotate(min_price=Min('variation__original_price')).order_by('min_price')
    elif sort=='high_to_low':
        products=products.annotate(min_price=Min('variation__original_price')).order_by('-min_price')
    else :
        products=Product.objects.all().order_by('-created_at')  

    paginator =Paginator(products,9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)          

    context={
        'products':products,
        'is_authenticated':is_authenticated,
        'current_sort':sort
    }
    return render(request,'shop.html',context)
def products(request):
    products=Product.objects.all()
    return render(request,'admin_templates/products.html',{'products':products})    
def delete_product(request):
    product=get_object_or_404(Product,id=product_id)
    product.status=False
    product.save()
    messages.success(request,"Product deleted successfully")
    return redirect('product')


def product_details(request, id):
    product = get_object_or_404(Product, id=id)
    variations = product.variation_set.all()
    product_images = product.productimages.all()
    highlights = product.highlights.all()

    # Calculate final prices
    for variation in variations:
        variation.final_price, variation.discount_percentage = get_best_price(variation)

    # Default variation for display
    if variations:
        default_variation = variations[0]
        default_final_price = default_variation.final_price
        default_discount = default_variation.discount_percentage
    else:
        default_final_price = None
        default_discount = 0

    # Total stock
    total_stock = sum(v.stock or 0 for v in variations)

    # Related products
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    for rel in related_products:
        first_var = rel.variation_set.first()
        if first_var:
            rel.final_price, rel.discount_percentage = get_best_price(first_var)
        else:
            rel.final_price, rel.discount_percentage = None, 0

    context = {
        "product": product,
        "variations": variations,
        "product_images": product_images,
        "default_final_price": default_final_price,
        "default_discount": default_discount,
        "related_products": related_products,
        "highlights": highlights,
        "total_stock": total_stock,
    }

    return render(request, "product_details.html", context)

def contact(request):
    return render(request,'contact.html')

def about(request):
    return render(request, 'about.html')
def add_offer(request):
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer_type = form.cleaned_data.get('offer_type')
            offer.save()  

            if offer_type == 'product':
                product_id = request.POST.get('product')
                if product_id:
                    try:
                        product = Product.objects.get(id=product_id)
                        product.offer = offer
                        product.save()
                    except Product.DoesNotExist:
                        pass

            elif offer_type == 'category':
                category_id = request.POST.get('category')
                if category_id:
                    try:
                        category = Category.objects.get(id=category_id)
                        offer.category = category
                        offer.save()
                    except Category.DoesNotExist:
                        pass

            messages.success(request, "Offer created successfully!")
            return redirect('offers_list')
    else:
        form = OfferForm()
    
    categories = Category.objects.all()
    products = Product.objects.all()    

    return render(request, 'admin_templates/add_offer.html', {
        'form': form,
        'categories': categories,
        'products': products
    })

@login_required
def offers_list(request):
    offers = Offer.objects.all().order_by('-id')

    search_offer = request.GET.get('q','')
    if search_offer :
        offers = offers.filter(title__icontains=search_offer)

    paginator =Paginator(offers,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,'admin_templates/offers_list.html',{'offers':offers,
    'page_obj':page_obj,
    'search_offer':search_offer})

@login_required
def edit_offer(request,id):
    offer = get_object_or_404(Offer,id=id)
    categories = Category.objects.all()
    products = Product.objects.all()

    if request.method == 'POST':
        offer.title = request.POST.get('title')
        offer.discount_type = request.POST.get('discount_type')
        offer.dis_value = request.POST.get('dis_value')
        offer.is_active = bool(request.POST.get('is_active'))
        offer.valid_from = request.POST.get('valid_from')
        offer.valid_to = request.POST.get('valid_to')
        offer.offer_type = request.POST.get('offer_type')
        offer.category_id = request.POST.get('category')
        offer.product_id = request.POST.get('product')

        offer.save()
        return redirect('offers_list')

    context = {
        'offer':offer,
        'categories':categories,
        'products':products,
    }    

    return render(request,'admin_templates/edit_offer.html',context)

@login_required
def delete_offer(request,id):
    offer_to = get_object_or_404(Offer,id=id)
    offer_to.delete()
    messages.success(request,'Offers deleted successfully.')
    return redirect('offers_list')
    return render(request,'admin_templates/admin_dashboard.html')    

@login_required(login_url='login')
def add_to_cart(request, product_id, size):
    product = get_object_or_404(Product, id=product_id)
    variation = get_object_or_404(Variation, product=product, size=size)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        size=size,
        defaults={'quantity': 1, 'unit_price': get_best_price(variation)[0]}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')

@login_required(login_url='login')

def cart(request):
    items = CartItem.objects.filter(user=request.user)

    
    for item in items:
        try:
            variation = Variation.objects.get(product=item.product, size=item.size)
            item.unit_price, _ = get_best_price(variation)  
        except Variation.DoesNotExist:
            item.unit_price = 0

        item.line_total = float(item.unit_price * item.quantity)

    context = {
        'items': items,
    }
    return render(request, 'cart.html', context)



@login_required(login_url='login')
def update_cart_item(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        item_id = data.get('id')
        quantity = max(1, int(data.get('quantity', 1)))

        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        item.quantity = quantity
        item.save()

    
        try:
            variation = Variation.objects.get(product=item.product, size=item.size)
            unit_price, _ = get_best_price(variation)
        except Variation.DoesNotExist:
            unit_price = 0

        line_total = float(unit_price * item.quantity)

        return JsonResponse({
            'item': {
                'id': item.id,
                'quantity': item.quantity,
                'line_total': line_total,
            }
        })

    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required(login_url='login')
def remove_cart_item(request, item_id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        cart_item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def coupon_list(request):
    coupons = Coupon.objects.all().order_by('-id')
    return render (request,'admin_templates/coupon_list.html',{'coupons':coupons})

def add_coupon(request):
    if request.method =="POST":
        code = request.POST.get('code')
        discount_amount = request.POST.get('discount_amount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')
        active = request.POST.get('active')=='on'

        if not code or not discount_amount:
            messages.error(request,'Please fill all fields')
            return redirect('add_coupon')

        Coupon.objects.create(
            code =code,
            discount_amount = discount_amount,
            valid_from = valid_from,
            valid_to = valid_to,
            active = active
        )    

        messages.success(request,"Coupon added successfully")
        return redirect('coupon_list')

    return render (request,'admin_templates/add_coupon.html')    

def edit_coupon(request,id):
    coupon = get_object_or_404(Coupon,id=id)

    if request.method == "POST":
        coupon.code = request.POST.get('code')
        coupon.discount_amount = request.POST.get('discount_amount')
        coupon.valid_from = request.POST.get('valid_from')
        coupon.valid_to = request.POST.get('valid_to')
        coupon.active = request.POST.get('active') == 'on'
        coupon.save()
        messages.success(request, "Coupon updated successfully!")
        return redirect('coupon_list')

    return render(request, 'admin_templates/edit_coupon.html', {'coupon': coupon})
      
@login_required(login_url='login')
def apply_coupon(request):
    if request.method == "POST":
        if request.POST.get('remove_coupon'):
            request.session.pop("coupon_id",None)
            messages.success(request,"Coupon removed successfully")
            return redirect('checkout')
        code = request.POST.get("coupon_code")
        if not code:
            messages.error(request,"Please enter a coupon code")
            return redirect('checkout')    
        try:
            coupon = Coupon.objects.get(
                code=code,
                active = True,
                valid_from__lte= timezone.now(),
                valid_to__gte= timezone.now()
            )       
            
            request.session["coupon_id"]= coupon.id     
            messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
            
        except Coupon.DoesNotExist:
             messages.error(request, "Invalid coupon code.")
    return redirect("checkout")

def add_to_wishlist(request):
    pass 

def wishlist(request):
    return render(request,'user/wishlist.html')

@login_required(login_url='login')
def buy_now(request, product_id, size):
    product = get_object_or_404(Product, id=product_id)
    variation = get_object_or_404(Variation, product=product, size=size)

    final_price, discount = get_best_price(variation)  

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        size=size,
        defaults={'quantity': 1, 'unit_price': final_price}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('checkout')

@login_required(login_url='login')
def check_out(request):
    user = request.user

    if request.method == "POST":
        
        selected_ids=request.POST.getlist('selected_items')
    else:
        selected_ids = CartItem.objects.filter(user=user).values_list('id', flat=True)

    if not selected_ids:
        messages.error(request, "Please select at least one item to checkout.")
        return redirect('cart')


    items = CartItem.objects.filter(user=user, id__in=selected_ids)

    subtotal=sum(item.unit_price * item.quantity for item in items)
    shipping=50 if subtotal>500 else 0
    discount=0
    coupon=None

    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            discount = coupon.discount_amount
        except Coupon.DoesNotExist:
            discount=0
            request.session.pop('coupon_id', None)

    total=subtotal-discount+shipping
        
    for item in items:
        item.line_total=item.unit_price*item.quantity

    user_addresses=Address.objects.filter(user=user)    

    context = {'items': items,
    'subtotal': subtotal,
    'shipping': shipping,
    'discount': discount,
    'total':total,
    'coupon': coupon,
    'user_addresses':user_addresses}
    return render(request, 'checkout.html', context)


@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        try:
            
            amount = int(float(request.POST.get("amount"))*100)
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payment = client.order.create({
                "amount": amount,  
                "currency": "INR",
                "payment_capture": "1",

            })
            return JsonResponse({
                'order':payment,
                'razorpay_key':settings.RAZORPAY_KEY_ID
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({'error':'Invalid request method'},status=400)        

def payment_success(request):
    return render(request,'user/payment_sucess.html')
def profile_view(request):
    user = request.user
    addresses = Address.objects.filter(user=user)

    return render(request, "user/profile.html", {
        "user": user,
        "addresses": addresses,
    
    })


def update_profile(request):
    if request.method=='POST':
        user=request.user
        profile = user.profile

        first_name=request.POST.get('first_name',user.first_name)
        last_name=request.POST.get('last_name',user.last_name)
        email=request.POST.get('email',user.email)
        phone=request.POST.get('phone',profile.phone)
        profile_photo = request.FILES.get('profile_photo')


        user.first_name=first_name
        user.last_name=last_name
        user.email=email
        
        user.save()
        profile = user.profile
        profile.phone=phone
        if profile_photo:
            profile.profile_photo = profile_photo
        profile.save()
       
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')

    return render(request, 'profile.html')
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    
    return render(request, "address_list.html", {"addresses": addresses})

login_required(login_url='login')
def add_address(request):
    if request.method=='POST':
        street=request.POST.get('street')
        city=request.POST.get('city')
        district=request.POST.get('district')
        state=request.POST.get('state')
        pincode=request.POST.get('pincode')
        
        is_default=request.POST.get('is_default')=='on'

        if is_default:
            Address.objects.filter(user=request.user,is_default=True).update(is_default=False)


        Address.objects.create(
            user=request.user,
            street=street,
            city=city,
            district=district,
            state=state,
            pincode=pincode,
            
            is_default=is_default

        )    

        return redirect('profile')
    return redirect('profile')
@login_required
def edit_address(request,address_id):
    address=get_object_or_404(Address,id=address_id,user=request.user)

    if request.method=='POST':
        address.street=request.POST.get('street')  
        address.city=request.POST.get('city') 
        address.district=request.POST.get('district') 
        address.state=request.POST.get('state') 
        address.pincode=request.POST.get('pincode') 
        address.street=request.POST.get('street') 
        
        address.is_default=request.POST.get('is_default')=='on'  
   
        if address.is_default:
            Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)
  
        address.save()
        return redirect('profile')

    return redirect('profile')    

@login_required
def remove_address(request,address_id):
    address=get_object_or_404(Address,id=address_id,user=request.user) 
    address.delete()
    return redirect('profile')   

@login_required
def set_default_address(request,address_id):
    Address.objects.filter(user=request.user,is_default=True).update(is_default=False)
    address=get_object_or_404(Address,id=address_id,user=request.user)
    address.is_default=True
    address.save()
    return redirect('profile')   




   

def wallet_view(request):
    wallet,created = Wallet.objects.get_or_create(user=request.user)
    return render(request,'user/wallet.html',{'wallet':wallet})

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
def add_money_to_wallet(request):
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))*100
        wallet, created = Wallet.objects.get_or_create(user=request.user)

        razorpay_order = client.order.create({
            'amount':int(amount),
            'currency':'INR',
            'payment_capture':'1'
        })

        return JsonResponse({
            "razorpay_order_id": razorpay_order["id"],
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "amount": amount
        })

    return JsonResponse({"error":"Invalid request"},status=400)      

@csrf_exempt
def wallet_payment_success(request):
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        amount = request.POST.get('amount')

        
        if payment_id and order_id and amount:
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            wallet.balance += Decimal(amount)
            wallet.save()
            

        return redirect('profile')
  
def myorders_view(request):
    user_orders=Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request,'user/myorders.html',{'user_orders':user_orders})
@login_required(login_url='login')
def place_orders(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        user = request.user
        
      
        cart_items = CartItem.objects.filter(user=user)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        order = Order.objects.create(user=user)    
        for item in cart_items:
            variation = item.product.variation_set.filter(size=item.size).first()
            if variation:
                price, _ = get_best_price(variation)
            else:
                price = item.unit_price
            OrderItem.objects.create(
                order=order,
                product = item.product,
                quantity = item.quantity,
                price = price
            )

        cart_items.delete()

        if payment_method == 'cod':
            order.payment_method = 'Cash on Delivery'
            order.status = 'Confirmed'  
            order.save()
            request.session['order_id'] = order.id
            return redirect('order_confirmation')

        elif payment_method == 'razorpay':
            return redirect('razorpay_payment')

        else:
            messages.error(request, "Invalid payment method selected.")
            return redirect('checkout')
    else:
        return redirect('cart')        
@login_required(login_url='login')
def order_confirmation(request):
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request,"No recent prder found")
        return redirect('cart')

    try:
        order = Order.objects.get(id=order_id,user=request.user)
        order_items = OrderItem.objects.filter(order=order)
    except Order.DoesNotExist:
        messages.error(request,"Order not found")
        return redirect('cart')

    context = {
        'order':order,
        'order_items':order_items,
    }    
    return render(request,'user/order_confirmation.html',context)

def logout_view(request):
    logout(request)
    request.session.flush()
    return render(request,'index.html')     


def login_error(request):
    messages.error(request, "There was an error during social authentication.")
    return redirect('login')


def order_list(request):
    orders=Order.objects.all().order_by("-created_at")
    return render(request,'admin_templates/order_list.html')


def download_invoice_pdf(request, order_id):
    pass
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    
    if Wishlist.objects.filter(user=request.user, product=product).exists():
        messages.info(request, "Product already in wishlist.")
    else:
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, "Product added successfully!")

    return redirect('wishlist')


def wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request,'user/wishlist.html',{"wishlist":wishlist})