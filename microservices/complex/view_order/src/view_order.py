from flask import Flask, jsonify, request

from flask_cors import CORS
from os import environ
from invokes import invoke_http

catalogue_url = environ.get('CATALOGUE_URL') or "http://catalogue:5004/api/v1/catalogue"
venue_url = environ.get('VENUE_URL') or "http://venue:5003/api/v1/venues"
order_url = environ.get('ORDER_URL') or "http://order:5006/api/v1/orders"

app = Flask(__name__)
CORS(app)

@app.route("/api/v1/orders", methods=["GET"])
def get_orders():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"code": 400, "message": "user_id is required."}), 400

    # Call order microservice
    # 1. get list of orders
    order_data = invoke_http(
        order_url,
        method="GET",
        params={"user_id": user_id},
    )
    if order_data["code"] not in range(200, 300):
        return jsonify({
            "code": order_data["code"],
            "message": order_data["message"]
        }), order_data["code"]
    result_json_to_return = {}
    # arranging order_items and venue details
    order_count = 0
    for order in order_data["orders"]:
        order_count += 1
        order_details = order
        item_count = 0
        for item in order["order_items"]:
            paid_item_price = item["item_price"]
            ordered_quantity = item["item_quantity"]
            item_id = item["item_id"]
            item_data = invoke_http(catalogue_url + "/" + item_id, method="GET")
            if item_data["code"] not in range(200, 300):
                return jsonify({
                    "code": item_data["code"],
                    "message": f'error from item.py: {item_data["message"]}'
                }), item_data["code"]

            item_details = item_data["data"]

            item_details["item_price"] = paid_item_price
            item_details["item_quantity"] = ordered_quantity

            # replace item details in order_items
            order_details["order_items"][item_count] = item_details

            item_count += 1

        # obtain venue details
        if "venue" in order:
            paid_venue_details = order["venue"]
            venue_id = paid_venue_details["venue_id"]

            paid_venue_price = paid_venue_details["venue_price"]
            booked_venue_date = paid_venue_details["venue_datetime"]

            venue_data = invoke_http(venue_url + "/" + venue_id, method="GET")
            if venue_data["code"] not in range(200, 300):
                return jsonify({
                    "code": venue_data["code"],
                    "message": f'error from venue.py: {venue_data["message"]}'
                }), venue_data["code"]

            venue_details = venue_data["data"]

            venue_details["venue_price"] = paid_venue_price
            venue_details["venue_datetime"] = booked_venue_date

            # replace venue details in venue
            order_details["venue"] = venue_details
            result_json_to_return[order_count] = order_details
        else:
            result_json_to_return[order_count] = order_details

    return jsonify({
        "code": 200,
        "user_id": user_id,
        "orders": result_json_to_return
    }
    ), 200


@app.route("/api/v1/orders/<order_id>", methods=["GET"])
def get_order_by_id(order_id):
    result_json_to_return = {}
    order_data_user_id = invoke_http(order_url + "/" + order_id, method="GET")
    if order_data_user_id["code"] not in range(200, 300):
        return jsonify({
            "code": order_data_user_id["code"],
            "message": f'error from order.py:{order_data_user_id["message"]}'
        }), order_data_user_id["code"]

    if len(order_data_user_id["order"]["order_items"]) > 0:
        count = 0
        for item in order_data_user_id["order"]["order_items"]:

            specific_item_id = item["item_id"]
            specific_item_details = invoke_http(catalogue_url + "/" + specific_item_id, method="GET")
            if specific_item_details["code"] not in range(200, 300):
                return jsonify({
                    "code": specific_item_details["code"],
                    "message": f'error from catalogue.py: {specific_item_details["message"]}'
                }), specific_item_details["code"]
            item_json = specific_item_details["data"]
            item_json["item_quantity"] = item["item_quantity"]
            order_data_user_id["order"]["order_items"][count] = item_json
            count += 1

        # specifically for venue
    if "venue" in order_data_user_id["order"]:

        venue_id = order_data_user_id["order"]["venue"]["venue_id"]
        specific_venue_details = invoke_http(venue_url + "/" + venue_id, method="GET")
        if specific_venue_details["code"] not in range(200, 300):
            return jsonify({
                "code": specific_venue_details["code"],
                "message": f'error from venue.py: {specific_venue_details["message"]}'
            }), specific_venue_details["code"]

        venue_json = specific_venue_details["data"]
        order_data_user_id["order"]["venue"] = venue_json

    result_json_to_return[order_id] = order_data_user_id["order"]

    return result_json_to_return, 200


if __name__ == "__main__":
    port = int(environ.get('PORT', 5300))
    app.run(host="0.0.0.0", port=port, debug=True)
