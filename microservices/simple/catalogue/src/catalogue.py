from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('catalogue_dbURL') or 'mysql+mysqlconnector://root@localhost:3306/catalogue'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalogue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

class Item(db.Model):
    __tablename__ = 'catalogue'

    item_id = db.Column(db.String, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    item_price = db.Column(db.Float(precision=2), nullable=False)
    item_img = db.Column(db.String(1000), nullable=False)
    item_description = db.Column(db.String(1000), nullable=False)
    item_rating = db.Column(db.Float(precision=2), nullable=False)
    review_count = db.Column(db.Integer, nullable=False)

    def __init__(self, item_id, category_name, item_name, item_price, item_img, item_description, item_rating, review_count):
        self.item_id = item_id
        self.category_name = category_name
        self.item_name = item_name
        self.item_price = item_price
        self.item_img = item_img
        self.item_description = item_description
        self.item_rating = item_rating
        self.review_count = review_count

    def json(self):
        return {"item_id": self.item_id, "category_name": self.category_name, "item_name" : self.item_name, "item_price" : self.item_price, "item_img" : self.item_img, "item_description": self.item_description, "item_rating" : self.item_rating, "review_count" : self.review_count}

with app.app_context():
  # call your method here
    db.create_all()

#get all items
@app.route("/api/v1/catalogue")
def get_all():
    print(request.cookies.get('user_id_email'))

    items = Item.query.all()
    if len(items):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "items": [item.json() for item in items]
                }
            }
        ), 200
    return jsonify(
        {
            "code": 404,
            "message": "There are no items."
        }
    ), 404

# get item by id
@app.route("/api/v1/catalogue/<string:item_id>")
def find_by_id(item_id):
    item = Item.query.filter_by(item_id=item_id).first()

    if item:
        return jsonify(
            {
                "code": 200,
                "data": item.json()
            }
        ), 200
    return jsonify(
        {
            "code": 404,
            "item_id": item_id,
            "message": "Item not found."
        }
    ), 404

# get item by category
@app.route("/api/v1/catalogue/category/<string:category>")
def find_by_category(category):
    items = Item.query.filter_by(category_name=category).all()
    if items:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "items": [item.json() for item in items]
                }
            }
        ), 200
    return jsonify(
        {
            "code": 404,
            "data": {
                "category": category
            },
            "message": "Items not found."
        }
    ), 404

# update item rating
@app.route("/api/v1/catalogue/update_item_rating", methods=['PUT'])
def update_rating():
    item_id = request.json['item_id']
    new_rating = request.json['rating']
    new_review_count = request.json["review_count"]
    item = Item.query.filter_by(item_id=item_id).first()
    if item:
        try:
            item.review_count = new_review_count
            item.item_rating = new_rating
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": item.json()
                }
            )
        except Exception as e:
            return jsonify(
                {
                    "code": 500,
                    "data": {
                        "item_id": item_id
                    },
                    "message": "An error occurred while updating the item." + str(e)
                }
            ), 500
    return jsonify(
        {
            "code": 404,
            "data": {
                "item_id": item_id
            },
            "message": "Item not found."
        }
    ), 404

if __name__ == '__main__':
    port = 5004 or int(environ.get('PORT', 5004))
    app.run(host="0.0.0.0",port=port, debug=True)
