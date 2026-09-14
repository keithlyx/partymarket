
import json
from flask import Flask, request, jsonify
import stripe
from flask_cors import CORS
from os import environ

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)

app.config['STRIPE_PUBLIC_KEY'] = environ.get('STRIPE_PUBLIC_KEY', '')
app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
stripe.api_key = environ.get('STRIPE_SECRET_KEY')


@app.route('/api/v1/stripepay', methods=['POST'])
def stripepay1():
    data = request.get_json()
    #print(data) return the json data
    token = data['token']
    print(f"charging token {token} for amount {data['amount']}")
    try:
        charge = stripe.Charge.create(
        amount=data['amount'],
        currency="sgd",
        source=token,
        description="My First Test Charge (created for API docs at https://www.stripe.com/docs/api)"
        )
        print(charge)
        receipt_url = charge['receipt_url']
        transaction_id = charge['id']
        return jsonify({
            'code': 200,
            'receipt_url': receipt_url,
            'order_id': transaction_id
        }), 200
    except Exception as e:
        print("Printing the error message:")
        try:
            error = json.loads(e)
            print("--JSON:", error)
        except Exception as e:
            print("--NOT JSON:", e)
            print("--RAW:", e)
        return jsonify({
            'code': 500,
            'message': 'An error occurred while processing the payment. Please try again.'
            }), 500
    
   #retrieve the receipt url from the charge object


@app.route('/api/v1/striperefund', methods=['POST'])
def striperefund():
    data = request.get_json()
    # data = json.loads(data)
    print("THIS IS PAYMENT", data)
    print(type(data))
    charge_id = data['charge_id']
    total_amount = data['amount']
    total_amount = int(float(total_amount) * 100)
    print(charge_id)
    print(type(total_amount))
    try:
        refund = stripe.Refund.create(
        charge = charge_id,
        amount = total_amount
        )
        print(refund)
        return jsonify({
                'code': 200,
                'refund': refund
                }), 200
    except Exception as e:
        print("Printing the error message:")
        try:
            error = json.loads(e)
            print("--JSON:", error)
        except Exception as e:
            print("--NOT JSON:", e)
            print("--RAW:", e)
        return jsonify({
            'code': 500,
            'message': 'An error occurred while processing the payment. Please try again.'
            }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5008,debug=True)
    #print("\nThis is " + os.path.basename(__file__), end='')
    #print(": monitoring routing key '{}' in exchange '{}' ...".format(monitorBindingKey, amqp_setup.exchangename))
   
