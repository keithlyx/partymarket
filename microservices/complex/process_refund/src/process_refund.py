from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ, path
from invokes import invoke_http
import amqp_setup
import pika
import json

app = Flask(__name__)
CORS(app)

payment_URL = environ.get('payment_URL') or "http://payment:5008/api/v1/refunds"
order_URL = environ.get('order_URL') or "http://order:5006/api/v1/orders"


@app.route('/api/v1/refunds', methods=["POST"])
def refund():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("order_id") or data.get("amount") is None:
        return jsonify({
            "code": 400,
            "message": "Request must include order_id and amount.",
        }), 400

    return process_refund(data)


def process_refund(data):
    order_id = data["order_id"]
    refund = invoke_http(payment_URL, method="POST", json={
        "charge_id": order_id,
        "amount": data["amount"],
    })
    if refund["code"] not in range(200, 300):
        return jsonify({
            "code": refund["code"],
            "message": "Payment provider rejected the refund request.",
        }), refund["code"]

    order = invoke_http(order_URL + "/" + order_id, method="PATCH", json={"status": "Refunded"})
    if order["code"] not in range(200, 300):
        return jsonify({
            "code": order["code"],
            "message": "Order status could not be updated after the refund.",
        }), order["code"]

    sendEmail(order["data"])
    return jsonify({
        "code": 200,
        "message": "Refund processed and notification queued.",
    }), 200

def sendEmail(order_details):
    # 3. send order to email microservice
    # Invoke the email microservice
    print('\n-----Sending to email queue-----')
    amqp_setup.check_setup()
    order_details["type"] = "order_refund"
    amqp_setup.channel.basic_publish(exchange="email_exchange", routing_key="confirmation.email",
                                     body=json.dumps(order_details), properties=pika.BasicProperties(delivery_mode=2))
    print("\n-----------Sent to email queue-----------\n")
    

if __name__ == "__main__":
    print("This is flask " + path.basename(__file__) + " for processing refunds...")
    port = 5700 or int(environ.get('PORT', 5700))
    app.run(host="0.0.0.0", port=port, debug=True)
