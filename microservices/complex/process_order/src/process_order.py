from flask import Flask, jsonify, request
from flask_cors import CORS
from os import environ, path
from invokes import invoke_http
import amqp_setup
import pika
import json

import datetime

payment_URL = environ.get('payment_URL') or 'http://payment:5008/api/v1/payments'
cart_URL = environ.get('cart_URL') or 'http://cart:5005/api/v1/carts'
order_URL = environ.get('order_URL') or 'http://order:5006/api/v1/orders'

app = Flask(__name__)

CORS(app)


# just to get all the cart details
@app.route("/api/v1/orders", methods=["POST"])
def create_order():
    # Simple check of input format and data of the request are JSON
    if request.is_json:
        try:
            order = request.get_json()
            print("\nReceived an order in JSON:", order)
            result = processOrder(order)
            print("Result: ", result)
            return result

        except Exception as e:
            return jsonify({
                "code": 404,
                "message": str(e)
            }), 404


    # if reached here, not a JSON request.
    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400


def processOrder(order):
    # 1. Send the order to payment microservice
    print("-----Processing order: ", order, '----------')
    amount = order["total_amount"]*100
    token = order["token"]
    print(f"invoking payment microservice with amount: {amount} and token: {token}")

    payment = invoke_http(payment_URL, method='POST', json={"token": token, "amount": amount})
    print(payment)
    if payment['code'] not in range(200, 300):
        return jsonify({
            "code": payment["code"],
            "message": "Error in payment microservice"
        }), payment["code"]

    print("\nPayment to stripe successful")
    order_id = payment["order_id"]
    receipt_url = payment["receipt_url"]
    print("Order of  ID: ", order_id, "generated.")

    #create order
    order["order_id"] = order_id
    order["order_datetime"] = datetime.datetime.now().strftime("%c")
    order["order_items"] = order["items"]
    order["receipt_url"] = receipt_url
    del order["items"]
    del order["token"]
    print("\nOrder to be sent to order microservice: ", order_id)
    #submit order
    result = invoke_http(order_URL, method='POST', json=order)
    if result["code"] not in range(200, 300):
        return jsonify({    
            "code": result["code"],
            "message": "Error in order microservice"
        }), result["code"]
    
    print("Order created successfully: ", order_id)
    # send email
    print("\nSending email to user: ", order["user_id"])
    sendEmail(order)
    print("\ndeleting cart for user: ", order["user_id"])
    delete_status = invoke_http(cart_URL+"/"+order["user_id"], method='DELETE')
    if delete_status["code"] not in range(200, 300):
        return jsonify({
            "code": delete_status["code"],
            "message": "Error in cart microservice"
        }), delete_status["code"]
    print("\nCart deleted successfully: ", order["user_id"])
    return jsonify({
        "code": 201,
        "message": "Order created successfully",
        "order_id": order_id
    }), 201


def sendEmail(order):
    # 3. send order to email microservice
    # Invoke the email microservice
    print('\n-----Sending to email queue-----')
    amqp_setup.check_setup()
    order["type"] = "order_confirmation"

    amqp_setup.channel.basic_publish(exchange="email_exchange", routing_key="confirmation.email",
                                     body=json.dumps(order), properties=pika.BasicProperties(delivery_mode=2))
    print("Sent to email queue")


if __name__ == "__main__":
    print("This is flask " + path.basename(__file__) + " for processing orders...")
    port = 5200 or int(environ.get('PORT', 5200))
    app.run(host="0.0.0.0", port=port, debug=True)
