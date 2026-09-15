from flask import make_response, request
import json

def create_cart_cookie(cookie_dict):
    cookie_json = json.dumps(cookie_dict)

    resp = make_response("Cookie set!")

    resp.set_cookie('cart_details', cookie_json)

    return resp


def create_checkout_cookie(delivery_address, delivery_date):
    cookie_dict = {
        'delivery_address': delivery_address,
        'delivery_date': delivery_date
    }

    cookie_json = json.dumps(cookie_dict)

    resp = make_response("Cookie set!")

    resp.set_cookie('checkout_details', cookie_json)

    return resp


def get_checkout_cookie(cookie_name):
    checkout_dict = {}

    checkout_cookie = request.cookies.get(cookie_name)
    if checkout_cookie:
        try:
            checkout_dict = json.loads(checkout_cookie)
        except (TypeError, ValueError):
            checkout_dict = {}

    return checkout_dict


def get_cart_cookie(cookie_name):
    cart_dict = {}

    cart_cookie = request.cookies.get(cookie_name)
    if cart_cookie:
        try:
            cart_dict = json.loads(cart_cookie)
        except (TypeError, ValueError):
            cart_dict = {}

    return cart_dict
