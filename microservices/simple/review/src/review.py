from datetime import datetime
from os import environ
from typing import Any, Optional, TypedDict

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///review.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class ReviewPayload(TypedDict):
    user_id: str
    prod_id: str
    rating: int
    rating_desc: str


def _validate_review(data: Any, require_identity: bool = True) -> Optional[str]:
    if not isinstance(data, dict):
        return "Request payload must be a JSON object."
    required_fields = ["rating", "rating_desc"]
    if require_identity:
        required_fields.extend(["user_id", "prod_id"])
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return "Missing required review fields: " + ", ".join(missing_fields) + "."
    for field in ("user_id", "prod_id") if require_identity else ():
        if not isinstance(data[field], str) or not data[field].strip():
            return field + " must be a non-empty string."
    if isinstance(data["rating"], bool) or not isinstance(data["rating"], int) or not 1 <= data["rating"] <= 5:
        return "rating must be an integer from one to five."
    if not isinstance(data["rating_desc"], str) or not data["rating_desc"].strip():
        return "rating_desc must be a non-empty string."
    return None


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
    validation_error = _validate_review(data)
    if validation_error:
        return jsonify({"code": 400, "message": validation_error}), 400

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
        created_date=datetime.now().isoformat(),
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
    validation_error = _validate_review(data, require_identity=False)
    if validation_error:
        return jsonify({"code": 400, "message": validation_error}), 400

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
    review.created_date = datetime.now().isoformat()
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
