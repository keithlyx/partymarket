from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ["CATALOGUE_DATABASE_URL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Item(db.Model):
    __tablename__ = 'catalogue'

    item_id = db.Column(db.String, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    item_price = db.Column(db.Numeric(10, 2), nullable=False)
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
        return {"item_id": self.item_id, "category_name": self.category_name, "item_name": self.item_name, "item_price": f"{self.item_price:.2f}", "item_img": self.item_img, "item_description": self.item_description, "item_rating": self.item_rating, "review_count": self.review_count}

@app.route("/api/v1/catalogue")
def get_catalogue():
    category = request.args.get("category")
    query = Item.query
    if category:
        query = query.filter_by(category_name=category)

    items = query.all()
    return jsonify(
        {
            "code": 200,
            "data": {
                "items": [item.json() for item in items]
            }
        }
    ), 200

# get item by id
@app.route("/api/v1/catalogue/<string:item_id>")
def get_item(item_id):
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

@app.route("/api/v1/catalogue/<string:item_id>/rating", methods=['PATCH'])
def update_item_rating(item_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "rating" not in data or "review_count" not in data:
        return jsonify({
            "code": 400,
            "message": "Request must include rating and review_count."
        }), 400

    new_rating = data['rating']
    new_review_count = data["review_count"]
    if (isinstance(new_rating, bool) or not isinstance(new_rating, (int, float))
            or not 0 <= new_rating <= 5
            or isinstance(new_review_count, bool) or not isinstance(new_review_count, int)
            or new_review_count < 0):
        return jsonify({
            "code": 400,
            "message": "rating must be between zero and five and review_count must be non-negative.",
        }), 400
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
        except Exception:
            db.session.rollback()
            return jsonify(
                {
                    "code": 500,
                    "data": {
                        "item_id": item_id
                    },
                    "message": "An error occurred while updating the item."
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
    port = int(environ.get('PORT', 5004))
    debug = environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host="0.0.0.0", port=port, debug=debug)
