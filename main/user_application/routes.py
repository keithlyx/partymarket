"""Import all web route modules so Flask registers their endpoints."""

from user_application.route_modules import auth, cart, catalogue, orders, reviews

__all__ = ["auth", "cart", "catalogue", "orders", "reviews"]
