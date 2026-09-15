from os import environ, path

from flask import Flask, jsonify, request
from flask_cors import CORS

from invokes import invoke_http


catalogue_url = environ.get("catalogue_URL") or "http://catalogue:5004/api/v1/catalogue"
venue_url = environ.get("venue_URL") or "http://venue:5003/api/v1/venues"
review_url = environ.get("review_URL") or "http://review:5007/api/v1/reviews"

app = Flask(__name__)
CORS(app)


def _downstream_error(response, message):
    code = response.get("code", 502)
    if code >= 500:
        code = 502
    return jsonify({"code": code, "message": message}), code


def _update_product_rating(product_id):
    reviews_response = invoke_http(
        review_url,
        method="GET",
        params={"product_id": product_id},
    )
    if reviews_response.get("code") not in range(200, 300):
        return _downstream_error(
            reviews_response,
            "Review service could not retrieve product reviews.",
        )

    reviews = reviews_response.get("data", {}).get("reviews", [])
    if not reviews:
        return jsonify({
            "code": 502,
            "message": "Review service returned no reviews after the update.",
        }), 502

    rating = round(sum(review["rating"] for review in reviews) / len(reviews), 2)
    rating_payload = {
        "rating": rating,
        "review_count": len(reviews),
    }
    if product_id.startswith("i"):
        rating_response = invoke_http(
            catalogue_url + "/" + product_id + "/rating",
            method="PATCH",
            json=rating_payload,
        )
    elif product_id.startswith("v"):
        rating_response = invoke_http(
            venue_url + "/" + product_id + "/rating",
            method="PATCH",
            json=rating_payload,
        )
    else:
        return jsonify({
            "code": 400,
            "message": "Product ID must identify a catalogue item or venue.",
        }), 400

    if rating_response.get("code") not in range(200, 300):
        return _downstream_error(
            rating_response,
            "Product rating could not be updated.",
        )
    return rating_response


@app.route("/api/v1/reviews", methods=["POST"])
def add_review():
    data = request.get_json(silent=True)
    required_fields = ("user_id", "prod_id", "rating", "rating_desc")
    if not isinstance(data, dict) or any(field not in data for field in required_fields):
        return jsonify({
            "code": 400,
            "message": "Request must include user_id, prod_id, rating, and rating_desc.",
        }), 400

    review_response = invoke_http(review_url, method="POST", json=data)
    if review_response.get("code") not in range(200, 300):
        return _downstream_error(review_response, "Review could not be created.")

    rating_response = _update_product_rating(data["prod_id"])
    if isinstance(rating_response, tuple):
        return rating_response

    return jsonify({
        "code": 201,
        "data": review_response.get("data"),
        "message": "Review created and product rating updated.",
    }), 201


@app.route("/api/v1/reviews/<user_id>/<prod_id>", methods=["PATCH"])
def update_review(user_id, prod_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "rating" not in data or "rating_desc" not in data:
        return jsonify({
            "code": 400,
            "message": "Request must include rating and rating_desc.",
        }), 400

    review_response = invoke_http(
        review_url + "/" + user_id + "/" + prod_id,
        method="PATCH",
        json=data,
    )
    if review_response.get("code") not in range(200, 300):
        return _downstream_error(review_response, "Review could not be updated.")

    rating_response = _update_product_rating(prod_id)
    if isinstance(rating_response, tuple):
        return rating_response

    return jsonify({
        "code": 200,
        "data": review_response.get("data"),
        "message": "Review updated and product rating recalculated.",
    }), 200


if __name__ == "__main__":
    print("This is flask " + path.basename(__file__) + " for processing all reviews.")
    port = int(environ.get("PORT", 5400))
    app.run(host="0.0.0.0", port=port)
