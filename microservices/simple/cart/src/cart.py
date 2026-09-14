from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('cart_dbURL') or 'mysql+mysqlconnector://root@localhost:3306/cart'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Cart_Item(db.Model):
    __tablename__ = 'cart_item'

    user_id = db.Column(db.String, primary_key=True)
    item_id = db.Column(db.String, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, item_id, quantity):
        self.user_id = user_id
        self.item_id = item_id
        self.quantity = quantity

    def json(self):
        return {"user_id": self.user_id, "item_id": self.item_id, "quantity": self.quantity}


class Cart_Venue(db.Model):
    __tablename__ = 'cart_venue'

    user_id = db.Column(db.String, primary_key=True)
    venue_id = db.Column(db.String, primary_key=True)
    datetime = db.Column(db.String, nullable=False)

    def __init__(self, user_id, venue_id, datetime):
        self.user_id = user_id
        self.venue_id = venue_id
        self.datetime = datetime

    def json(self):
        return {"user_id": self.user_id, "venue_id": self.venue_id, "datetime": self.datetime}


with app.app_context():
    # call your method here
    db.create_all()


# adding item to cart
@app.route("/api/v1/add_cart/<user_id>/<prod_id>", methods=['POST'])
def add_to_cart(user_id, prod_id):
    if request.is_json:
        prod_data = request.get_json()
        # if item is being added to cart
        if prod_id[0] == "i":
            quantity_res = prod_data["quantity"]
            cart_item = Cart_Item.query.filter_by(user_id=user_id, item_id=prod_id).first()
            print(cart_item)
            # if user has already added the item to cart, update quantity
            if cart_item:
                cart_item.quantity = cart_item.quantity + 1


            # if user has not added the item to cart, add item to cart
            else:
                cart_item = Cart_Item(user_id=user_id, item_id=prod_id, quantity=quantity_res)
                db.session.add(cart_item)
            try:
                db.session.commit()
                return jsonify(
                    {
                        "code": 201,
                        "message": "Item added to cart.",
                    }
                ), 201
            except Exception as e:
                return jsonify(
                    {
                        "code": 500,
                        "message": "An error occurred while adding item to cart." + str(e)
                    }
                ), 500
        # if venue is being added to cart
        elif prod_id[0] == "v":

            cart_venue = Cart_Venue.query.filter_by(user_id=user_id).first()
            # if user has already booked a venue
            if cart_venue and cart_venue.venue_id != prod_id:
                return jsonify(
                    {
                        "code": 400,
                        "message": "You have already booked a venue."
                    }
                ), 400
            else:
                venue_datetime = prod_data["venue_datetime"]
                cart_venue = Cart_Venue(user_id=user_id, venue_id=prod_id, datetime=venue_datetime)
                try:
                    db.session.add(cart_venue)
                    db.session.commit()
                    return jsonify(
                        {
                            "code": 201,
                            "message": "Venue added to cart.",
                        }
                    ), 201
                except Exception as e:
                    return jsonify(
                        {
                            "code": 500,
                            "message": "An error occurred while adding venue to cart." + str(e)
                        }
                    ), 500

        else:
            return jsonify(
                {
                    "code": 400,
                    "message": "invalid product or venue id"
                }
            ), 400
    else:
        return jsonify(
            {
                "code": 400,
                "message": "The request payload is not in JSON format"
            }
        ), 400


# getting cart information by user_id
@app.route("/api/v1/get_cart/<user_id>", methods=['GET'])
def get_cart(user_id):
    cart_items = Cart_Item.query.filter_by(user_id=user_id).all()
    cart_venues = Cart_Venue.query.filter_by(user_id=user_id).all()

    if len(cart_items) or len(cart_venues):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "cart_items": [cart_item.json() for cart_item in cart_items],
                    "cart_venue": [cart_venue.json() for cart_venue in cart_venues]
                }
            }
        ), 200
    return jsonify(
        {
            "code": 404,
            "message": "There are no items in the cart."
        }
    ), 404


@app.route("/api/v1/remove-from-cart/<product_id>/<user_id>", methods=['POST'])
def delete_item(product_id, user_id):
    # catalogue cart
    if product_id[0] == "i":
        cart_item = Cart_Item.query.filter_by(user_id=user_id, item_id=product_id).first()
        db.session.delete(cart_item)
        try:

            db.session.commit()

            return jsonify(
                {
                    "code": 200,
                    "message": "Item deleted."
                }
            ), 200
        except Exception as e:
            db.session.rollback()
            return jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred while deleting item." + str(e)
                }
            ), 500
    # venue cart
    else:
        cart_venue = Cart_Venue.query.filter_by(user_id=user_id, venue_id=product_id).first()
        db.session.delete(cart_venue)
        try:
            db.session.commit()

            return jsonify(
                {
                    "code": 200,
                    "message": "Item deleted."
                }
            ), 200
        except Exception as e:
            db.session.rollback()
            return jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred while deleting item." + str(e)
                }
            ), 500


@app.route("/api/v1/increase-cart-quantity/<product_id>/<user_id>", methods=['POST'])
def increase_quantity(product_id, user_id):
    # catalogue cart
    if product_id[0] == "i":
        cart_item = Cart_Item.query.filter_by(user_id=user_id, item_id=product_id).first()
        cart_item.quantity = cart_item.quantity + 1
        try:
            db.session.commit()

            return jsonify(
                {
                    "code": 200,
                    "message": "Item quantity increased."
                }
            ), 200
        except Exception as e:
            db.session.rollback()
            return jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred while increasing item quantity." + str(e)
                }
            ), 500
    # venue cart
    elif product_id[0] == "v":
        return jsonify(
            {
                "code": 400,
                "message": "Venue quantity cannot be increased."
            }
        ), 400
    else:
        return jsonify(
            {
                "code": 400,
                "message": "Invalid product id."
            }
        ), 400


@app.route("/api/v1/decrease-cart-quantity/<product_id>/<user_id>", methods=['POST'])
def decrease_quantity(product_id, user_id):
    # catalogue cart
    if product_id[0] == "i":
        cart_item = Cart_Item.query.filter_by(user_id=user_id, item_id=product_id).first()
        cart_item.quantity = cart_item.quantity - 1
        try:
            db.session.commit()

            return jsonify(
                {
                    "code": 200,
                    "message": "Item quantity decreased."
                }
            ), 200
        except Exception as e:
            db.session.rollback()
            return jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred while decreasing item quantity." + str(e)
                }
            ), 500
    # venue cart
    else:
        return jsonify(
            {
                "code": 400,
                "message": "Venue quantity cannot be decreased."
            }
        ), 400


@app.route("/api/v1/delete_cart/<user_id>", methods=['POST'])
def delete_cart(user_id):
    cart_items = Cart_Item.query.filter_by(user_id=user_id).all()
    cart_venues = Cart_Venue.query.filter_by(user_id=user_id).all()

    for cart_item in cart_items:
        db.session.delete(cart_item)
    for cart_venue in cart_venues:
        db.session.delete(cart_venue)
    try:
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": "Cart is empty."
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while deleting cart." + str(e)
            }
        ), 500


if __name__ == '__main__':
    port = 5005 or int(environ.get('PORT', 5005))
    app.run(host="0.0.0.0", port=port, debug=True)
