from os import environ

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ["CART_DATABASE_URL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class CartItem(db.Model):
    __tablename__ = 'cart_item'

    user_id = db.Column(db.String, primary_key=True)
    item_id = db.Column(db.String, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, item_id, quantity):
        self.user_id = user_id
        self.item_id = item_id
        self.quantity = quantity

    def json(self):
        return {
            "user_id": self.user_id,
            "item_id": self.item_id,
            "quantity": self.quantity,
        }


class CartVenue(db.Model):
    __tablename__ = 'cart_venue'

    user_id = db.Column(db.String, primary_key=True)
    venue_id = db.Column(db.String, primary_key=True)
    datetime = db.Column(db.String, nullable=False)

    def __init__(self, user_id, venue_id, datetime):
        self.user_id = user_id
        self.venue_id = venue_id
        self.datetime = datetime

    def json(self):
        return {
            "user_id": self.user_id,
            "venue_id": self.venue_id,
            "datetime": self.datetime,
        }


@app.route("/api/v1/carts/<user_id>/products/<prod_id>", methods=["POST"])
def add_to_cart(user_id, prod_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "code": 400,
            "message": "Request payload must be a JSON object.",
        }), 400

    if prod_id.startswith("i"):
        quantity = data.get("quantity")
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            return jsonify({
                "code": 400,
                "message": "Item quantity must be an integer.",
            }), 400

        if quantity < 1:
            return jsonify({
                "code": 400,
                "message": "Item quantity must be at least one.",
            }), 400

        cart_item = CartItem.query.filter_by(
            user_id=user_id,
            item_id=prod_id,
        ).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            db.session.add(CartItem(
                user_id=user_id,
                item_id=prod_id,
                quantity=quantity,
            ))

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({
                "code": 500,
                "message": "An error occurred while adding the item to the cart.",
            }), 500

        return jsonify({
            "code": 201,
            "message": "Item added to cart.",
        }), 201

    if prod_id.startswith("v"):
        venue_datetime = data.get("venue_datetime")
        if not venue_datetime:
            return jsonify({
                "code": 400,
                "message": "Venue datetime is required.",
            }), 400

        cart_venue = CartVenue.query.filter_by(user_id=user_id).first()
        if cart_venue and cart_venue.venue_id != prod_id:
            return jsonify({
                "code": 409,
                "message": "A user can only book one venue.",
            }), 409

        if cart_venue:
            cart_venue.datetime = venue_datetime
        else:
            db.session.add(CartVenue(
                user_id=user_id,
                venue_id=prod_id,
                datetime=venue_datetime,
            ))

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({
                "code": 500,
                "message": "An error occurred while adding the venue to the cart.",
            }), 500

        return jsonify({
            "code": 201,
            "message": "Venue added to cart.",
        }), 201

    return jsonify({
        "code": 400,
        "message": "Invalid product ID.",
    }), 400


@app.route("/api/v1/carts/<user_id>", methods=["GET"])
def get_cart(user_id):
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    cart_venues = CartVenue.query.filter_by(user_id=user_id).all()
    return jsonify({
        "code": 200,
        "data": {
            "cart_items": [cart_item.json() for cart_item in cart_items],
            "cart_venues": [cart_venue.json() for cart_venue in cart_venues],
        },
    }), 200


@app.route("/api/v1/carts/<user_id>/products/<product_id>", methods=["DELETE"])
def delete_item(user_id, product_id):
    if product_id.startswith("i"):
        cart_record = CartItem.query.filter_by(
            user_id=user_id,
            item_id=product_id,
        ).first()
    elif product_id.startswith("v"):
        cart_record = CartVenue.query.filter_by(
            user_id=user_id,
            venue_id=product_id,
        ).first()
    else:
        return jsonify({"code": 400, "message": "Invalid product ID."}), 400

    if not cart_record:
        return jsonify({"code": 404, "message": "Cart item not found."}), 404

    db.session.delete(cart_record)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred while deleting the cart item.",
        }), 500

    return jsonify({"code": 200, "message": "Cart item deleted."}), 200


@app.route("/api/v1/carts/<user_id>/items/<item_id>", methods=["PATCH"])
def update_quantity(user_id, item_id):
    if not item_id.startswith("i"):
        return jsonify({
            "code": 400,
            "message": "Only catalogue items have quantities.",
        }), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "quantity" not in data:
        return jsonify({
            "code": 400,
            "message": "Request must include quantity.",
        }), 400

    quantity = data["quantity"]
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        return jsonify({
            "code": 400,
            "message": "Quantity must be an integer.",
        }), 400

    if quantity < 1:
        return jsonify({
            "code": 400,
            "message": "Quantity must be at least one.",
        }), 400

    cart_item = CartItem.query.filter_by(
        user_id=user_id,
        item_id=item_id,
    ).first()
    if not cart_item:
        return jsonify({"code": 404, "message": "Cart item not found."}), 404

    cart_item.quantity = quantity
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred while updating the cart item.",
        }), 500

    return jsonify({"code": 200, "data": cart_item.json()}), 200


@app.route("/api/v1/carts/<user_id>", methods=["DELETE"])
def delete_cart(user_id):
    CartItem.query.filter_by(user_id=user_id).delete()
    CartVenue.query.filter_by(user_id=user_id).delete()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred while deleting the cart.",
        }), 500

    return jsonify({"code": 200, "message": "Cart is empty."}), 200


if __name__ == '__main__':
    port = int(environ.get('PORT', 5005))
    debug = environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host="0.0.0.0", port=port, debug=debug)
