from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ



app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('venue_dbURL') or 'mysql+mysqlconnector://root@localhost:3306/venue'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///venue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CORS(app)
class Venue(db.Model):
    __tablename__ = 'venue'

    venue_id = db.Column(db.String, primary_key=True)
    venue_name = db.Column(db.String, nullable=False)
    venue_img = db.Column(db.String, nullable=False)
    venue_description = db.Column(db.String, nullable=False)
    venue_price = db.Column(db.Float(precision=2), nullable=False)
    venue_rating = db.Column(db.Float(precision=2), nullable=False)
    review_count = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String, nullable=False)

    def __init__(self, venue_id, venue_name, venue_img, venue_description,
                 venue_price, venue_rating, review_count, address):
        self.venue_id = venue_id
        self.venue_name = venue_name
        self.venue_img = venue_img
        self.venue_description = venue_description
        self.venue_price = venue_price
        self.venue_rating = venue_rating
        self.review_count = review_count
        self.address = address

    def json(self):
        print(self.address)
        return {"venue_id": self.venue_id, "venue_name": self.venue_name,
                "venue_img": self.venue_img, "venue_description": self.venue_description,
                "venue_price": self.venue_price, "venue_rating": self.venue_rating,
                "review_count": self.review_count, "address": self.address}

with app.app_context():
  # call your method here
    db.create_all()

@app.route("/api/v1/venues")
def get_all():
    venues = Venue.query.all()
    return jsonify(
        {
            "code": 200,
            "data": {
                "venues": [venue.json() for venue in venues]
            }
        }
    ), 200

@app.route("/api/v1/venues/<string:venue_id>")
def find_by_venue_id(venue_id):
    venue = Venue.query.filter_by(venue_id=venue_id).first()
    if venue:
        return jsonify(
            {
                "code": 200,
                "data": venue.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                "venue_id": venue_id
            },
            "message": f"Venue of id:{venue_id} not found."
        }
    ), 404

@app.route("/api/v1/venues/<string:venue_id>/rating", methods=["PATCH"])
def update_venue_rating(venue_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "rating" not in data or "review_count" not in data:
        return jsonify({
            "code": 400,
            "message": "Request must include rating and review_count."
        }), 400

    new_rating = data['rating']
    new_review_count = data["review_count"]
    venue = Venue.query.filter_by(venue_id=venue_id).first()
    if venue:
        try:
            venue.review_count = new_review_count
            venue.venue_rating = new_rating
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": venue.json(),
                    "message": "Venue rating updated."
                }
            ), 200
        except Exception as e:
            db.session.rollback()
            return jsonify(
                {
                    "code": 500,
                    "venue_id": venue_id,
                    "message": "An error occurred updating the venue rating."
                }
            ), 500

    return jsonify(
        {
            "code": 404,
            "venue_id": venue_id,
            "message": "Venue not found."
        }
    ), 404

if __name__ == '__main__':
    port = 5003 or int(environ.get('PORT', 5003))
    app.run(host="0.0.0.0",port=port, debug=True)
