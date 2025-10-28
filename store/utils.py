from django.utils import timezone

def get_best_price(variation):
    """
    Returns the best price and discount for a variation,
    considering product-level and category-level offers only.
    """
    best_price = variation.original_price
    best_discount = 0
    now = timezone.now()

    # 1. Check product offer
    product_offer = variation.product.offer
    if product_offer and product_offer.is_active and product_offer.valid_from <= now <= product_offer.valid_to:
        if product_offer.discount_type == 'flat':
            discount_amount = product_offer.dis_value
        else:  # percentage
            discount_amount = variation.original_price * product_offer.dis_value / 100
        price = variation.original_price - discount_amount
        discount = round(discount_amount / variation.original_price * 100)
        if price < best_price:
            best_price = price
            best_discount = discount

    # 2. Check category offers
    category = variation.product.category
    if category:
        for offer in category.offer_on_this_category.filter(is_active=True, valid_from__lte=now, valid_to__gte=now):
            if offer.discount_type == 'flat':
                discount_amount = offer.dis_value
            else:
                discount_amount = variation.original_price * offer.dis_value / 100
            price = variation.original_price - discount_amount
            discount = round(discount_amount / variation.original_price * 100)
            if price < best_price:
                best_price = price
                best_discount = discount

    return round(best_price, 2), best_discount
