from flask import Flask, jsonify, request

from os import environ
from invokes import invoke_http
from order_enricher import OrderEnrichmentError, enrich_order

catalogue_url = environ.get('CATALOGUE_URL') or "http://catalogue:5004/api/v1/catalogue"
venue_url = environ.get('VENUE_URL') or "http://venue:5003/api/v1/venues"
order_url = environ.get('ORDER_URL') or "http://order:5006/api/v1/orders"

app = Flask(__name__)

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
    # Add current item and venue descriptions without replacing paid values.
    for order in order_data["orders"]:
        try:
            order_details = enrich_order(
                order,
                fetch_catalogue_item=lambda item_id: invoke_http(catalogue_url + "/" + item_id, method="GET"),
                fetch_venue=lambda venue_id: invoke_http(venue_url + "/" + venue_id, method="GET"),
            )
        except OrderEnrichmentError as error:
            return jsonify({"code": error.status_code, "message": error.message}), error.status_code
        result_json_to_return[order["order_id"]] = order_details

    return jsonify({
        "code": 200,
        "data": {
            "user_id": user_id,
            "orders": result_json_to_return,
        },
    }
    ), 200


@app.route("/api/v1/orders/<order_id>", methods=["GET"])
def get_order_by_id(order_id):
    order_data_user_id = invoke_http(order_url + "/" + order_id, method="GET")
    if order_data_user_id["code"] not in range(200, 300):
        return jsonify({
            "code": order_data_user_id["code"],
            "message": f'error from order.py:{order_data_user_id["message"]}'
        }), order_data_user_id["code"]

    try:
        order_details = enrich_order(
            order_data_user_id["order"],
            fetch_catalogue_item=lambda item_id: invoke_http(catalogue_url + "/" + item_id, method="GET"),
            fetch_venue=lambda venue_id: invoke_http(venue_url + "/" + venue_id, method="GET"),
        )
    except OrderEnrichmentError as error:
        return jsonify({"code": error.status_code, "message": error.message}), error.status_code

    return jsonify({
        "code": 200,
        "data": {
            "user_id": order_data_user_id.get("user_id"),
            "order": order_details,
        },
    }), 200


if __name__ == "__main__":
    port = int(environ.get('PORT', 5300))
    debug = environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host="0.0.0.0", port=port, debug=debug)
