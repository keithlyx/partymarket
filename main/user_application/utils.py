from flask import Flask, make_response, request, jsonify
import json

def create_cart_cookie(cookie_dict):
    print('============= create_cart_cookie function ==============')
    # set cookie
    cookie_json = json.dumps(cookie_dict)

    resp = make_response("Cookie set!")

    resp.set_cookie('cart_details', cookie_json)

    print(resp)

    return resp


def create_checkout_cookie(delivery_address, delivery_date):
    print('============= create_checkout_cookie function ==============')
    # set cookie
    cookie_dict = {
        'delivery_address': delivery_address,
        'delivery_date': delivery_date
    }

    cookie_json = json.dumps(cookie_dict)

    resp = make_response("Cookie set!")

    resp.set_cookie('checkout_details', cookie_json)

    print(resp)

    return resp


def get_checkout_cookie(cookie_name):
    print('============= get_checkout_cookie function ==============')
    # get cookie
    checkout_dict = {}

    checkout_cookie = request.cookies.get(cookie_name)
    if checkout_cookie:
        checkout_dict = json.loads(checkout_cookie)
        # print(checkout_dict)
    else:
        print('Checkout cookie not found')

    return checkout_dict


def get_cart_cookie(cookie_name):
    print('============= get_cart_cookie function ==============')
    # get cookie
    cart_dict = {}

    cart_cookie = request.cookies.get(cookie_name)
    if cart_cookie:
        cart_dict = json.loads(cart_cookie)
        # print(cart_dict)
    else:
        print('Cart cookie not found')

    return cart_dict