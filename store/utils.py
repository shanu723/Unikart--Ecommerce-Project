from django.utils import timezone

def get_best_price(variation):

    original_price = variation.original_price
    best_price = original_price
    best_discount = 0

    now = timezone.localtime()

    all_offers = variation.product.offer_on_this_product.all()

    product_offers = variation.product.offer_on_this_product.filter(
        is_active=True,
        valid_from__lte=now,
        valid_to__gte=now
    )
    
    for offer in product_offers:
      
        if offer.discount_type == "flat":
            discount_amount = min(offer.dis_value, original_price)
        else:
            discount_amount = (original_price * offer.dis_value) / 100

        price = original_price - discount_amount
        price = max(price, 0)

        discount = round((discount_amount / original_price) * 100) if original_price else 0

        if price < best_price:
            best_price = price
            best_discount = discount

   
    category = variation.product.category

    if category:

        category_offers = category.offer_on_this_category.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        )
     
        for offer in category_offers:

            if offer.discount_type == "flat":
                discount_amount = min(offer.dis_value, original_price)
            else:
                discount_amount = (original_price * offer.dis_value) / 100

            price = original_price - discount_amount
            price = max(price, 0)

            discount = round((discount_amount / original_price) * 100) if original_price else 0

            if price < best_price:
                best_price = price
                best_discount = discount


    return round(best_price, 2), best_discount