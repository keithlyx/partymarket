
import logging
from flask import Flask, request, jsonify
import stripe
from os import environ

app = Flask(__name__)


app.config['STRIPE_PUBLIC_KEY'] = environ.get('STRIPE_PUBLIC_KEY', '')
app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
stripe.api_key = environ.get('STRIPE_SECRET_KEY')
logger = logging.getLogger(__name__)


@app.route('/api/v1/payments', methods=['POST'])
def create_payment():
    data = request.get_json(silent=True)
    if (not isinstance(data, dict) or not data.get('token')
            or isinstance(data.get('amount_cents'), bool)
            or not isinstance(data.get('amount_cents'), int)
            or data.get('amount_cents') <= 0):
        return jsonify({
            'code': 400,
            'message': 'Request must include a payment token and positive amount_cents.'
        }), 400

    token = data['token']
    try:
        charge = stripe.Charge.create(
        amount=data['amount_cents'],
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


@app.route('/api/v1/refunds', methods=['POST'])
def create_refund():
    data = request.get_json(silent=True)
    if (not isinstance(data, dict) or not data.get('charge_id')
            or isinstance(data.get('amount_cents'), bool)
            or not isinstance(data.get('amount_cents'), int)
            or data.get('amount_cents') <= 0):
        return jsonify({
            'code': 400,
            'message': 'Request must include a charge ID and positive amount_cents.'
        }), 400

    charge_id = data['charge_id']
    amount_cents = data['amount_cents']
    try:
        refund = stripe.Refund.create(
        charge = charge_id,
        amount = amount_cents
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
    port = int(environ.get("PORT", 5008))
    debug = environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host="0.0.0.0", port=port, debug=debug)
   
