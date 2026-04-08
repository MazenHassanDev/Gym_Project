from models.membership_options_model import MembershipOption

# ===========================================================================
# Discounts & Joining Fees
# ===========================================================================

JOINING_FEES = {
    'ugym': 10.00,
    'powerzone': 30.00
}

DISCOUNT_RATES = {
    'ugym': {
        'student': 0.20,
        'pensioner': 0.15
    },
    'powerzone': {
        'student': 0.15,
        'pensioner': 0.20
    }
}
      
# ===========================================================================
# Calculate Monthly Total
# ===========================================================================

def calculate_total(gym_name, gym_access, gym_addons, is_student, is_pensioner, sessiondb):

    total = 0.00
    user_items = []

    discount_type = 'student' if is_student else ('pensioner' if is_pensioner else None)
    discount_rate = DISCOUNT_RATES[gym_name.lower()].get(discount_type, 0) if discount_type else 0

    has_gym_access = gym_access is not None

    if gym_access:
        option = sessiondb.query(MembershipOption).filter_by(gym_name=gym_name.lower(), option_code=gym_access).first()

        if option:
            price = float(option.price_without_gym)
            
            if option.discountable and discount_rate:
                price = round(price * (1 - discount_rate), 2)

            total += price
            user_items.append({'display_name': option.display_name, 'price': price})

    for addon_code in gym_addons:
        option = sessiondb.query(MembershipOption).filter_by(gym_name=gym_name.lower(), option_code=addon_code).first()

        if option:
            price = float(option.price_with_gym) if has_gym_access else float(option.price_without_gym)

            if option.discountable and discount_rate:
                price = round(price * (1 - discount_rate), 2)

            total += price
            user_items.append({'display_name': option.display_name, 'price': price})

    return round(total, 2), user_items