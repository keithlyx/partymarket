from decimal import Decimal, InvalidOperation

from user_application import app


CATALOGUE_URL = app.config['CATALOGUE_SERVICE_URL']
VENUE_URL = app.config['VENUE_SERVICE_URL']
CART_URL = app.config['CART_SERVICE_URL']
REVIEW_URL = app.config['REVIEW_SERVICE_URL']
PROCESS_REVIEW_URL = app.config['PROCESS_REVIEW_SERVICE_URL']
VIEW_ORDER_URL = app.config['VIEW_ORDER_SERVICE_URL']
PROCESS_ORDER_URL = app.config['PROCESS_ORDER_SERVICE_URL']
REFUND_URL = app.config['REFUND_SERVICE_URL']


def as_money(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")
