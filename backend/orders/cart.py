from django.shortcuts import get_object_or_404
from market.models import Product

SESSION_KEY = "cart"

def get_cart(session):
    return session.get(SESSION_KEY, {})

def save_cart(session, cart):
    session[SESSION_KEY] = cart
    session.modified = True

def add_to_cart(session, product_id, qty=1):
    cart = get_cart(session)
    cart[str(product_id)] = cart.get(str(product_id), 0) + int(qty)
    save_cart(session, cart)

def set_quantity(session, product_id, qty):
    cart = get_cart(session)
    
    if int(qty) <= 0:
        if str(product_id) in cart:
            del cart[str(product_id)]
    else:
        cart[str(product_id)] = int(qty)
    
    save_cart(session, cart)
    
def remove_from_cart(session, product_id):
    cart = get_cart(session)
    cart.pop(str(product_id), None)
    save_cart(session, cart)

def clear_cart(session):
    if SESSION_KEY in session:
        del session[SESSION_KEY]
        session.modified = True

def cart_items_and_total(session):
    cart = get_cart(session)
    items = []
    total = 0
    for pid, qty in cart.items():
        product = get_object_or_404(Product, pk=int(pid))
        items.append({
            "product":product,
            "quantity":qty,
            "unit_price_inr":product.price,
            "total":product.price * qty
        }) 
        total += product.price * qty
    
    return items, total

