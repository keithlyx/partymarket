from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ, path
from invokes import invoke_http
import amqp_setup
import pika
import json
import threading

app = Flask(__name__)
CORS(app) 

app.config["THREADING"] = True

payment_URL = environ.get('payment_URL') or "http://payment:5008/api/v1/striperefund"
order_URL = environ.get('order_URL') or "http://order:5006/api/v1/"
getorder_URL = environ.get('getorder_URL') or "http://order:5006/api/v1/get_order/"
@app.route('/api/v1/refund', methods=["POST"])
def refund_():
    print(request)
    if request.is_json:
        #retrieve the charge id from the url
        try:
            order_id = request.get_json()
            result = processRefund(order_id)
            # print(result)
            result = json.loads(result[0].data)

            return jsonify(result), result["code"]
        
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


def processRefund(order_id):
    print(f'\n-----Processing refund for order_id: {order_id}-----')
    data = request.get_json()
    charge_id = data['chargeId']
    amount = data['totalAmountElement']
    refund = invoke_http(payment_URL, method="POST", json={"charge_id": charge_id , "amount": amount })
    if refund["code"] not in range(200, 300):
        return jsonify({
            "code": refund["code"],
            "message": "Error in payment microservice while refunding" + refund["message"]
        }), refund["code"]
    print("Refund result:", refund)
    # invoke the order microservie to update the order status
    print("Sending to order microservice to update status")
    order_id = order_id["chargeId"]
    order = invoke_http(order_URL + '/update_order_status/' + order_id, method="POST", json={"status": "Refunded"})
    print("Updated to refunded")
    if order["code"] not in range(200, 300):
        return jsonify({
            "code": order["code"],
            "message": "Error in order microservice while updating status" + order["message"]
        }), order["code"]
    print("-----Sending to email queue-----")
    amqp_thread = threading.Thread(target=sendEmail(order['data']))
    amqp_thread.start()
    return jsonify({
        "code": 200,
        "message": "Refund process ends here sent to email queue"
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
