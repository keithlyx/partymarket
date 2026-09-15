
import logging
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
logger = logging.getLogger(__name__)


@app.route('/api/v1/stripepay', methods=['POST'])
def stripepay1():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get('token') or data.get('amount') is None:
        return jsonify({
            'code': 400,
            'message': 'Request must include a payment token and amount.'
        }), 400

    token = data['token']
    try:
        charge = stripe.Charge.create(
        amount=data['amount'],
        currency="sgd",
        source=token,
        description="My First Test Charge (created for API docs at https://www.stripe.com/docs/api)"
        )
        receipt_url = charge['receipt_url']
        transaction_id = charge['id']
        return jsonify({
            'code': 200,
            'receipt_url': receipt_url,
            'order_id': transaction_id
        }), 200
    except stripe.error.StripeError:
        logger.exception("Stripe payment failed")
        return jsonify({
            'code': 502,
            'message': 'An error occurred while processing the payment. Please try again.'
            }), 502
    except Exception:
        logger.exception("Unexpected payment error")
        return jsonify({
            'code': 500,
            'message': 'An unexpected error occurred while processing the payment.'
        }), 500
    
   #retrieve the receipt url from the charge object


@app.route('/api/v1/striperefund', methods=['POST'])
def striperefund():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get('charge_id') or data.get('amount') is None:
        return jsonify({
            'code': 400,
            'message': 'Request must include a charge ID and amount.'
        }), 400

    charge_id = data['charge_id']
    total_amount = data['amount']
    total_amount = int(float(total_amount) * 100)
    try:
        refund = stripe.Refund.create(
        charge = charge_id,
        amount = total_amount
        )
        return jsonify({
                'code': 200,
                'refund_id': refund['id'],
                'status': refund['status']
                }), 200
    except stripe.error.StripeError:
        logger.exception("Stripe refund failed")
        return jsonify({
            'code': 502,
            'message': 'An error occurred while processing the payment. Please try again.'
            }), 502
    except Exception:
        logger.exception("Unexpected refund error")
        return jsonify({
            'code': 500,
            'message': 'An unexpected error occurred while processing the refund.'
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5008,debug=True)
    #print("\nThis is " + os.path.basename(__file__), end='')
    #print(": monitoring routing key '{}' in exchange '{}' ...".format(monitorBindingKey, amqp_setup.exchangename))
   
