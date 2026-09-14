from flask import Flask, jsonify, request
from flask_cors import CORS
from os import environ,path
from invokes import invoke_http
import json

app = Flask(__name__)   
CORS(app)
catalogue_URL = environ.get('catalogue_URL') or "http://catalogue:5004/api/v1/catalogue"
venue_URL = environ.get('venue_URL') or "http://venue:5003/api/v1/venue"
review_URL = environ.get('review_URL') or "http://review:5007/api/v1"


@app.route("/api/v1/review/add_review/<user_id>/<prod_id>", methods=["POST"])
def add_review(user_id, prod_id):
    print("=================process_review.py add_review called! =================")
    if request.is_json:
        review_str = request.get_json()
        review_json = json.loads(review_str)
        print("updating review for user_id: " + user_id + " and prod_id: " + prod_id)
        review_response = invoke_http(review_URL + "/review/add_review/" + user_id + "/" + prod_id, method='POST', json=json.dumps(review_json))
        print(review_response["message"])
        if review_response["code"] not in range(200, 300):
            return jsonify({
                "code": review_response["code"],
                "message": "Error from review microservice." + review_response["message"]
            }), review_response["code"]

        if prod_id[0] == "i":
            print("updating item rating")
            final_response = update_item_rating(prod_id, review_json)
            if final_response["code"] not in range(200, 300):
                return jsonify({
                    "code": final_response["code"],
                    "message": "Error from catalogue microservice." + final_response["message"]
                }), final_response["code"]
            print(final_response["message"])

        elif prod_id[0] == "v":
            print("updating venue rating")
            final_response = update_venue_rating(prod_id, review_json)
            if final_response["code"] not in range(200, 300):
                return jsonify({
                    "code": final_response["code"],
                    "message": "Error from venue microservice." + final_response["message"]
                }), final_response["code"]
            print(final_response["message"])
        print("review processed successfully")
        return review_response

    return jsonify({
        "code": 400,
        "message": "Request body must be JSON"
    }
    ), 400


@app.route("/api/v1/review/edit_review/<user_id>/<prod_id>", methods=['PUT'])
def update_review(user_id, prod_id):
    print("=================process_review.py edit_review called! =================")
    if request.is_json:
        review_json = request.get_json()
        print("updating review for user_id: " + user_id + " and prod_id: " + prod_id)
        review_response = invoke_http(review_URL + "/review/edit_review/" + user_id + "/" + prod_id, method='PUT', json=review_json)
        print(review_response["message"])
        if review_response["code"] not in range(200, 300):
            return jsonify({
                "code": review_response["code"],
                "message": "Error from review microservice." + review_response["message"]
            }), review_response["code"]

        if prod_id[0] == "i":
            print("updating item rating")
            final_response = update_edit_item_rating(prod_id, review_json)
            if final_response["code"] not in range(200, 300):
                return jsonify({
                    "code": final_response["code"],
                    "message": "Error from catalogue microservice." + final_response["message"]
                }), final_response["code"]
            print(final_response["message"])
        elif prod_id[0] == "v":
            print("updating venue rating")
            final_response = update_edit_venue_rating(prod_id, review_json)
            if final_response["code"] not in range(200, 300):
                return jsonify({
                    "code": final_response["code"],
                    "message": "Error from venue microservice." + final_response["message"]
                }), final_response["code"]
            print(final_response["message"])

        print("review processed successfully")
        return review_response
    return jsonify({
        "code": 400,
        "message": "Request body must be JSON"
    }
    ), 400


# Function to route to catalog to edit the rating
def update_item_rating(prod_id, review_json):
    result_json_to_pass = {}
    item_data = invoke_http(catalogue_URL + "/" + prod_id, method="GET")
    if item_data["code"] not in range(200, 300):
        return jsonify({
            "code": item_data["code"],
            "message": "Error from catalogue microservice while retrieving item." + item_data["message"]
        }
        ), item_data["code"]
    # old
    item_details = item_data["data"]
    item_rating = item_details["item_rating"]
    review_count = item_details["review_count"]
    # new
    input_rating = review_json["rating"]

    new_review_count = review_count + 1
    new_rating = round((item_rating * review_count + input_rating) / new_review_count, 2)

    result_json_to_pass["item_id"] = prod_id
    result_json_to_pass["rating"] = new_rating
    result_json_to_pass["review_count"] = new_review_count

    update_response = invoke_http(catalogue_URL + "/update_item_rating", method="PUT", json=result_json_to_pass)
    if update_response["code"] not in range(200, 300):
        return jsonify({
            "code": update_response["code"],
            "message": "Error from catalogue microservice while updating rating." + update_response["message"]
        }
        ), update_response["code"]

    return update_response


def update_venue_rating(prod_id, review_json):
    result_json_to_pass = {}
    venue_data = invoke_http(venue_URL + "/" + prod_id, method="GET")
    if venue_data["code"] not in range(200, 300):
        return jsonify({
            "code": venue_data["code"],
            "message": "Error from venue microservice while retrieving venue." + venue_data["message"]
        }
        ), venue_data["code"]
    # old
    venue_details = venue_data["data"]
    venue_rating = venue_details["venue_rating"]
    review_count = venue_details["review_count"]
    # new
    input_rating = review_json["rating"]
    
    new_review_count = review_count + 1
    new_rating = round((venue_rating * review_count + input_rating) / new_review_count, 2)

    result_json_to_pass["venue_id"] = prod_id
    result_json_to_pass["rating"] = new_rating
    result_json_to_pass["review_count"] = new_review_count

    update_response = invoke_http(venue_URL + "/update_venue_rating", method="PUT", json=result_json_to_pass)
    if update_response["code"] not in range(200, 300):
        return jsonify({
            "code": update_response["code"],
            "message": "Error from venue microservice while updating rating." + update_response["message"]
        }
        ), update_response["code"]

    return update_response



# Function for edit_review
def update_edit_item_rating(prod_id, review_json):
    result_json_to_pass = {}
    old_item_data = invoke_http(catalogue_URL + "/" + prod_id, method="GET")
    if old_item_data["code"] not in range(200, 300):
        return jsonify({
            "code": old_item_data["code"],
            "message": "Error from catalogue microservice while retrieving item." + old_item_data["message"]
        }
        ), old_item_data["code"]
    old_item_details = old_item_data["data"]
    old_item_rating = old_item_details["item_rating"]
    review_count = old_item_details["review_count"]
    input_rating = review_json["rating"]
    
    if review_count == 1:
        result_json_to_pass["item_id"] = prod_id
        result_json_to_pass["rating"] = input_rating
        result_json_to_pass["review_count"] = 1
        update_response = invoke_http(catalogue_URL + "/update_item_rating", method="PUT", json=result_json_to_pass)

    else:
        result_json_to_pass["item_id"] = prod_id
        all_review_json = invoke_http(review_URL + "/review/" + prod_id, method="GET")
        if all_review_json["code"] in range(200, 300):
            new_rating = round((old_item_rating * review_count) / len(all_review_json["review"]), 2)

            result_json_to_pass["rating"] = new_rating
            result_json_to_pass["review_count"] = review_count

            update_response = invoke_http(catalogue_URL + "/update_item_rating", method="PUT", json=result_json_to_pass)
            if update_response["code"] in range(200, 300):
                return jsonify({
                    "code": update_response["code"],
                    "message": "Successfully updated rating."
                })

            return update_response
       
        else:
            return jsonify({
            "code": update_response["code"],
            "message": "Error from catalogue microservice while updating rating." + update_response["message"]
            }
        ), update_response["code"]

    return update_response


def update_edit_venue_rating(prod_id, review_json):
    result_json_to_pass = {}
    old_venue_data = invoke_http(venue_URL + "/" + prod_id, method="GET")
    if old_venue_data["code"] not in range(200, 300):
        return jsonify({
            "code": old_venue_data["code"],
            "message": "Error from venue microservice while retrieving venue." + old_venue_data["message"]
        }
        ), old_venue_data["code"]
    
    # old
    old_venue_details = old_venue_data["data"]
    old_venue_rating = old_venue_details["venue_rating"]
    review_count = old_venue_details["review_count"]

    # new
    input_rating = review_json["rating"]
    
    if review_count == 1:
        result_json_to_pass["venue_id"] = prod_id
        result_json_to_pass["rating"] = input_rating
        result_json_to_pass["review_count"] = 1
        update_response = invoke_http(venue_URL + "/update_venue_rating", method="PUT", json=result_json_to_pass)
    
    else:
        result_json_to_pass["venue_id"] = prod_id
        all_review_json = invoke_http(review_URL + "/review/" + prod_id, method="GET")
        if all_review_json["code"] in range(200, 300):
            new_rating = round((old_venue_rating * review_count) / len(all_review_json["review"]), 2)
            result_json_to_pass["rating"] = new_rating
            result_json_to_pass["review_count"] = review_count

            update_response = invoke_http(venue_URL + "/update_venue_rating", method="PUT", json=result_json_to_pass)
            if update_response["code"] not in range(200, 300):
                return jsonify({
                    "code": update_response["code"],
                    "message": "Error from venue microservice while updating rating." + update_response["message"]
                }
                ), update_response["code"]

    return update_response



if __name__ == "__main__":
    print("This is flask " + path.basename(__file__) +
          " for processing all reviews.")
    port = 5400 or int(environ.get('PORT', 5400))
    app.run(host="0.0.0.0", port=port, debug=True)
