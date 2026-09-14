from os import environ
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

db = SQLAlchemy(app)
CORS(app)


class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    total_amount = db.Column(db.Float(precision=2), nullable=False)
    order_datetime = db.Column(db.String(255), nullable=False)
    order_status = db.Column(db.String(255), nullable=False)
    delivery_address = db.Column(db.String(255), nullable=False)
    delivery_datetime = db.Column(db.String(255), nullable=False)

    def __init__(self, order_id, user_id, total_amount, order_datetime, order_status, delivery_address,
                 delivery_datetime):
        self.order_id = order_id
        self.user_id = user_id
        self.total_amount = total_amount
        self.order_datetime = order_datetime
        self.order_status = order_status
        self.delivery_address = delivery_address
        self.delivery_datetime = delivery_datetime

    def json(self):
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "total_amount": self.total_amount,
            "order_datetime": self.order_datetime,
            "order_status": self.order_status,
            "delivery_address": self.delivery_address,
            "delivery_datetime": self.delivery_datetime

        }


class OrderItems(db.Model):
    __tablename__ = 'order_items'
    order_id = db.Column(db.String(255), primary_key=True)
    item_id = db.Column(db.String(255), primary_key=True)
    item_quantity = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Float(precision=2), nullable=False)

    def __init__(self, order_id, item_id, item_quantity, item_price):
        self.order_id = order_id
        self.item_id = item_id
        self.item_quantity = item_quantity
        self.item_price = item_price

    def json(self):
        return {
            "order_id": self.order_id,
            "item_id": self.item_id,
            "item_quantity": self.item_quantity,
            "item_price": self.item_price
        }


class OrderVenue(db.Model):
    __tablename__ = 'order_venue'
    order_id = db.Column(db.String(255), primary_key=True)
    venue_id = db.Column(db.String(255), primary_key=True)
    venue_price = db.Column(db.Float(precision=2), nullable=False)
    venue_datetime = db.Column(db.String(255), nullable=False)

    def __init__(self, order_id, venue_id, venue_price, venue_datetime):
        self.order_id = order_id
        self.venue_id = venue_id
        self.venue_price = venue_price
        self.venue_datetime = venue_datetime

    def json(self):
        return {
            "order_id": self.order_id,
            "venue_id": self.venue_id,
            "venue_price": self.venue_price,
            "venue_datetime": self.venue_datetime
        }


with app.app_context():
    # call your method here
    db.create_all()


# get list of orders by user id
@app.route("/api/v1/get_orders/<string:user_id>", methods=['GET'])
def get_orders(user_id):
    # user_id = request.args.get("user_id")
    orders = Orders.query.filter_by(user_id=user_id).all()
    order_json = [detail.json() for detail in orders]
    if orders:
        temp_orders = []
        for order in order_json:
            temp = {
                "order_id": order["order_id"],
                "total_amount": order["total_amount"],
                "order_datetime": order["order_datetime"],
                "order_status": order["order_status"],
                "delivery_address": order["delivery_address"],
                "order_items": [],
            }
            order_id = order["order_id"]
            order_items = OrderItems.query.filter_by(order_id=order_id).all()

            order_items_json = [detail.json() for detail in order_items]

            for item in order_items_json:
                temp["order_items"].append({
                    "item_id": item["item_id"],
                    "item_quantity": item["item_quantity"],
                    "item_price": item["item_price"]
                })

            order_venue = OrderVenue.query.filter_by(order_id=order_id).all()

            order_venue_json = [detail.json() for detail in order_venue]

            for venue in order_venue_json:
                temp["venue"] = {
                    "venue_id": venue["venue_id"],
                    "venue_price": venue["venue_price"],
                    "venue_datetime": venue["venue_datetime"]
                }
            temp_orders.append(temp)
        print(temp_orders)

        return jsonify(
            {
                "code": 200,
                "user_id": user_id,
                "orders": temp_orders
            }
        ),200
    return jsonify(
        {
            "code": 404,
            "user_id": user_id,
            "message": f"No orders for user id {user_id} found."
        }
    ), 404


@app.route("/api/v1/get_order/<order_id>", methods=['GET'])
def get_order(order_id):
    # order_id = request.args.get("order_id")
    order = Orders.query.filter_by(order_id=order_id).first()
    order = order.json()
    if order:
        temp = {
            "order_id": order["order_id"],
            "total_amount": order["total_amount"],
            "order_datetime": order["order_datetime"],
            "order_status": order["order_status"],
            "delivery_address": order["delivery_address"],
            "order_items": [],

        }
        order_items = OrderItems.query.filter_by(order_id=order_id).all()
        order_items_json = [detail.json() for detail in order_items]

        order_venue = OrderVenue.query.filter_by(order_id=order_id).all()
        order_venue_json = [detail.json() for detail in order_venue]

        for item in order_items_json:
            temp["order_items"].append({
                "item_id": item["item_id"],
                "item_quantity": item["item_quantity"],
                "item_price": item["item_price"]
            })

        for venue in order_venue_json:
            temp["venue"] = {
                "venue_id": venue["venue_id"],
                "venue_price": venue["venue_price"],
                "venue_datetime": venue["venue_datetime"]
            }
        print(temp)
        return jsonify(
            {
                "code": 200,
                "order": temp
            }
        ), 200
    return jsonify(
        {
            "code": 404,
            "order_id": order_id,
            "message": f"No order with id {order_id} found."
        }
    ), 404


@app.route("/api/v1/create_order", methods=['POST'])
def create_order():
    data = request.get_json()
    data = json.loads(data)
    print(data)
    status = "Accepted"

    order = Orders(order_id=data["order_id"], user_id=data["user_id"], total_amount=data["total_amount"],
                   order_datetime=data["order_datetime"], order_status=status,
                   delivery_address=data["delivery_address"], delivery_datetime=data["delivery_datetime"])
    print(data)
    db.session.add(order)

    for item in data["order_items"]:
        order_item = OrderItems(order_id=data["order_id"], item_id=item["item_id"],
                                item_quantity=item["item_quantity"],
                                item_price=item["item_price"])
        db.session.add(order_item)
    # print(data["venue"])
    if 'venue' in data:
        order_venue = OrderVenue(order_id=data["order_id"], venue_id=data["venue"]["venue_id"],
                                venue_price=data["venue"]["venue_price"],
                                venue_datetime=data["venue"]["venue_datetime"])

        db.session.add(order_venue)
    # if order_venue in db.session.new:
    #     print('The order has been added to the session')
    # else:
    #     print('The order has not been added to the session')
    try:
        db.session.commit()
        return jsonify({
            "code": 201,
            "data": data
        }), 201

    except Exception as e:
        db.session.rollback()  # Roll back the session to discard the changes that caused the error
        return jsonify({
            "code": 500,
            "message": "An error occurred while creating the order. " + str(e)
        }), 500


@app.route("/api/v1/update_order_status/<order_id>/", methods=['POST'])
def update_order(order_id):
    data = request.get_json()
    print(data)
    order = Orders.query.filter_by(order_id=order_id).first()
    if order:
        order.order_status = data["status"]
        try:
            db.session.commit()
            return jsonify({
                "code": 201,
                "data": order.json()
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "code": 500,
                "message": "An error occurred while updating the order. " + str(e)
            }), 500
    return jsonify({
        "code": 404,
        "message": f"No order with id {order_id} found."
    }), 404


if __name__ == '__main__':
    port = 5006 or int(environ.get('PORT', 5006))
    app.run(host="0.0.0.0", port=port, debug=True)
