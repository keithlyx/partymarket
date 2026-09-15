from datetime import datetime
from os import environ

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///review.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Review_db(db.Model):
    __tablename__ = 'review_items'

    user_id = db.Column(db.String, primary_key=True)
    prod_id = db.Column(db.String, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    rating_desc = db.Column(db.String, nullable=False)
    created_date = db.Column(db.String, nullable=False)

    def __init__(self, user_id, prod_id, rating, rating_desc, created_date):
        self.user_id = user_id
        self.prod_id = prod_id
        self.rating = rating
        self.rating_desc = rating_desc
        self.created_date = created_date

    def json(self):
        return {
            "user_id": self.user_id,
            "prod_id": self.prod_id,
            "rating": self.rating,
            "rating_desc": self.rating_desc,
            "created_date": self.created_date,
        }


with app.app_context():
    db.create_all()


@app.route("/api/v1/reviews", methods=["GET"])
def get_reviews():
    product_id = request.args.get("product_id")
    user_id = request.args.get("user_id")
    if not product_id and not user_id:
        return jsonify({
            "code": 400,
            "message": "product_id or user_id is required.",
        }), 400

    query = Review_db.query
    if product_id:
        query = query.filter_by(prod_id=product_id)
    if user_id:
        query = query.filter_by(user_id=user_id)

    reviews = query.all()
    return jsonify({
        "code": 200,
        "data": {
            "reviews": [review.json() for review in reviews],
        },
    }), 200


@app.route("/api/v1/reviews/<user_id>/<prod_id>", methods=["GET"])
def get_review(user_id, prod_id):
    review = Review_db.query.filter_by(
        user_id=user_id,
        prod_id=prod_id,
    ).first()
    if not review:
        return jsonify({
            "code": 404,
            "message": "Review not found.",
        }), 404

    return jsonify({
        "code": 200,
        "data": review.json(),
    }), 200


@app.route("/api/v1/reviews", methods=["POST"])
def add_review():
    data = request.get_json(silent=True)
    required_fields = ("user_id", "prod_id", "rating", "rating_desc")
    if not isinstance(data, dict) or any(field not in data for field in required_fields):
        return jsonify({
            "code": 400,
            "message": "Request must include user_id, prod_id, rating, and rating_desc.",
        }), 400

    existing_review = Review_db.query.filter_by(
        user_id=data["user_id"],
        prod_id=data["prod_id"],
    ).first()
    if existing_review:
        return jsonify({
            "code": 409,
            "message": "This product has already been reviewed by the user.",
        }), 409

    review = Review_db(
        user_id=data["user_id"],
        prod_id=data["prod_id"],
        rating=data["rating"],
        rating_desc=data["rating_desc"],
        created_date=datetime.now(),
    )
    db.session.add(review)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred while creating the review.",
        }), 500

    return jsonify({
        "code": 201,
        "data": review.json(),
    }), 201


@app.route("/api/v1/reviews/<user_id>/<prod_id>", methods=["PATCH"])
def update_review(user_id, prod_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "rating" not in data or "rating_desc" not in data:
        return jsonify({
            "code": 400,
            "message": "Request must include rating and rating_desc.",
        }), 400

    review = Review_db.query.filter_by(
        user_id=user_id,
        prod_id=prod_id,
    ).first()
    if not review:
        return jsonify({
            "code": 404,
            "message": "Review not found.",
        }), 404

    review.rating = data["rating"]
    review.rating_desc = data["rating_desc"]
    review.created_date = datetime.now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": "An error occurred while updating the review.",
        }), 500

    return jsonify({
        "code": 200,
        "data": review.json(),
    }), 200


if __name__ == '__main__':
    port = int(environ.get('PORT', 5007))
    app.run(host="0.0.0.0", port=port, debug=True)
