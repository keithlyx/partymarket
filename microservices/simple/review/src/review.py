from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
from datetime import datetime

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('review_dbURL') or 'mysql+mysqlconnector://root@localhost:3306/review'
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
        return {"user_id": self.user_id, "prod_id": self.prod_id,
                "rating": self.rating, "rating_desc": self.rating_desc, "created_date": self.created_date}


with app.app_context():
    # call your method here
    db.create_all()


# need add methods to CRUD review
# getting review information by prod_id
@app.route("/api/v1/review/product/<prod_id>")
def get_review_by_prod_id(prod_id):
    review = Review_db.query.filter_by(prod_id=prod_id).all()
    print(review)
    if review:
        return jsonify(
            {
                "code": 200,
                "prod_id": prod_id,
                "data": {
                    "review": [review.json() for review in review]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": f"no reviews of item: {prod_id} found."
        }
    ), 404


# getting review information by user_id, uses GET method
@app.route("/api/v1/review/user/<user_id>", methods=['GET'])
def get_review_by_user_id(user_id):
    reviews = Review_db.query.filter_by(user_id=user_id).all()
    if reviews:
        return jsonify(
            {
                "code": 200,
                "user_id": user_id,
                "data": {
                    "review": [review.json() for review in reviews]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": f"no reviews by user: {user_id} found."
        }
    ), 404


# Check if user has entered a review for a specific product
@app.route("/api/v1/review/<user_id>/<prod_id>", methods=["GET"])
def get_review_by_composite_id(user_id, prod_id):
    review = Review_db.query.filter_by(user_id=user_id, prod_id=prod_id).all()
    if review:
        return jsonify(
            {
                "code": 200,
                "user_id": user_id,
                "data": {
                    "review": [review.json() for review in review]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": f"no reviews by user: {user_id} found."
        }
    ), 404


# adding review information
@app.route("/api/v1/review/add_review/<user_id>/<prod_id>", methods=["POST"])
def add_review(user_id, prod_id):
    print("=================review.py add_review called! =================")
    review = Review_db.query.filter_by(user_id=user_id, prod_id=prod_id).all()
    if len(review) > 0:
        return jsonify(
            {
                "code": 404,
                "message": f"{prod_id} has already been reviewed found by {user_id}!"
            }
        ), 404

    else:
        if request.is_json:
            review_json = request.get_json()
            print(type(review_json))
            print(f'=================review_json: {review_json} =================')
            print(user_id, prod_id, review_json["rating"], review_json["rating_desc"])
            time_now = datetime.now()
            user_review = Review_db(user_id=user_id, prod_id=prod_id, rating=review_json['rating'],
                                    rating_desc=review_json["rating_desc"], created_date=time_now)
            try:
                db.session.add(user_review)
                db.session.commit()
                return jsonify({
                    "code": 200,
                    "message": f"Review of {prod_id} by {user_id} added."
                }), 200

            except Exception as e:
                db.session.rollback()
                return jsonify({
                    "code": 500,
                    "message": str(e)
                }), 500

        return jsonify(
            {
                "code": 404,
                "message": f"Request must be a JSON object."
            }
        ), 404


# update review information by user_id, uses PUT method
@app.route("/api/v1/review/edit_review/<user_id>/<prod_id>", methods=['PUT'])
def update_review(user_id, prod_id):
    # retrieve the item record to update
    if request.is_json:
        user_old_review = Review_db.query.filter_by(user_id=user_id, prod_id=prod_id).first()
        if user_old_review:
            user_new_review = request.get_json()

            try:
                user_old_review.rating = user_new_review["rating"]
                user_old_review.rating_desc = user_new_review["rating_desc"]
                user_old_review.created_date = datetime.now()
                db.session.commit()
                return jsonify(
                    {
                        "code": 200,
                        "message": f"Review of {prod_id} has been updated!"
                    }
                )

            except Exception as e:
                return jsonify({
                    "code": 400,
                    "message": "Review update failed." + str(e)
                }), 400

    return jsonify({
        "code": 400,
        "message": "Review update failed. Request must be a JSON object."
    }), 400


if __name__ == '__main__':
    port = 5007 or int(environ.get('PORT', 5007))
    app.run(host="0.0.0.0", port=port, debug=True)
