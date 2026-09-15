from os import environ
from typing import Any

from flask import Flask, jsonify, request

from invokes import invoke_http


catalogue_url = environ.get("CATALOGUE_URL") or "http://catalogue:5004/api/v1/catalogue"
venue_url = environ.get("VENUE_URL") or "http://venue:5003/api/v1/venues"
review_url = environ.get("REVIEW_URL") or "http://review:5007/api/v1/reviews"

app = Flask(__name__)


def _downstream_error(response: Any, message):
    code = response.get("code", 502) if isinstance(response, dict) else 502
    if code >= 500:
        code = 502
    return jsonify({"code": code, "message": message}), code


def _update_product_rating(product_id):
    reviews_response = invoke_http(
        review_url,
        method="GET",
        params={"product_id": product_id},
    )
    if not isinstance(reviews_response, dict) or reviews_response.get("code") not in range(200, 300):
        return _downstream_error(
            reviews_response,
            "Review service could not retrieve product reviews.",
        )

    review_data = reviews_response.get("data")
    reviews = review_data.get("reviews", []) if isinstance(review_data, dict) else []
    if not isinstance(reviews, list) or not reviews:
        return jsonify({
            "code": 502,
            "message": "Review service returned no reviews after the update.",
        }), 502

    if any(
        not isinstance(review, dict)
        or isinstance(review.get("rating"), bool)
        or not isinstance(review.get("rating"), (int, float))
        for review in reviews
    ):
        return jsonify({
            "code": 502,
            "message": "Review service returned invalid ratings.",
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

    if not isinstance(rating_response, dict) or rating_response.get("code") not in range(200, 300):
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
    validation_error = _validate_review(data)
    if validation_error:
        return jsonify({"code": 400, "message": validation_error}), 400

    review_response = invoke_http(review_url, method="POST", json=data)
    if review_response.get("code") not in range(200, 300):
        return _downstream_error(review_response, "Review could not be created.")

    rating_response = _update_product_rating(data["prod_id"])
    if isinstance(rating_response, tuple):
        rollback = invoke_http(
            review_url + "/" + data["user_id"] + "/" + data["prod_id"],
            method="DELETE",
        )
        if not isinstance(rollback, dict) or rollback.get("code") not in range(200, 300):
            return jsonify({
                "code": 502,
                "message": "Review was created but could not be rolled back after rating update failure.",
            }), 502
        return rating_response

    return jsonify({
        "code": 201,
        "data": review_response.get("data"),
        "message": "Review created and product rating updated.",
    }), 201


@app.route("/api/v1/reviews/<user_id>/<prod_id>", methods=["PATCH"])
def update_review(user_id, prod_id):
    data = request.get_json(silent=True)
    validation_error = _validate_review(data, require_identity=False)
    if validation_error:
        return jsonify({"code": 400, "message": validation_error}), 400
    if not (prod_id.startswith("i") or prod_id.startswith("v")):
        return jsonify({
            "code": 400,
            "message": "Product ID must identify a catalogue item or venue.",
        }), 400

    previous_review = invoke_http(
        review_url + "/" + user_id + "/" + prod_id,
        method="GET",
    )
    if not isinstance(previous_review, dict) or previous_review.get("code") not in range(200, 300):
        return _downstream_error(previous_review, "Review could not be retrieved before updating.")

    review_response = invoke_http(
        review_url + "/" + user_id + "/" + prod_id,
        method="PATCH",
        json=data,
    )
    if review_response.get("code") not in range(200, 300):
        return _downstream_error(review_response, "Review could not be updated.")

    rating_response = _update_product_rating(prod_id)
    if isinstance(rating_response, tuple):
        previous_data = previous_review.get("data")
        rollback = invoke_http(
            review_url + "/" + user_id + "/" + prod_id,
            method="PATCH",
            json=previous_data,
        )
        if not isinstance(rollback, dict) or rollback.get("code") not in range(200, 300):
            return jsonify({
                "code": 502,
                "message": "Review was updated but could not be restored after rating update failure.",
            }), 502
        return rating_response

    return jsonify({
        "code": 200,
        "data": review_response.get("data"),
        "message": "Review updated and product rating recalculated.",
    }), 200


def _validate_review(data, require_identity=True):
    if not isinstance(data, dict):
        return "Request payload must be a JSON object."
    required_fields = ["rating", "rating_desc"]
    if require_identity:
        required_fields.extend(["user_id", "prod_id"])
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return "Missing required review fields: " + ", ".join(missing_fields) + "."
    if require_identity:
        for field in ("user_id", "prod_id"):
            if not isinstance(data[field], str) or not data[field].strip():
                return field + " must be a non-empty string."
    if isinstance(data["rating"], bool) or not isinstance(data["rating"], int) or not 1 <= data["rating"] <= 5:
        return "rating must be an integer from one to five."
    if not isinstance(data["rating_desc"], str) or not data["rating_desc"].strip():
        return "rating_desc must be a non-empty string."
    if require_identity and not (data["prod_id"].startswith("i") or data["prod_id"].startswith("v")):
        return "prod_id must identify a catalogue item or venue."
    return None


if __name__ == "__main__":
    port = int(environ.get("PORT", 5400))
    app.run(host="0.0.0.0", port=port)
