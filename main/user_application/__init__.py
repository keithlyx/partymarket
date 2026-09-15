from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from os import environ
from pathlib import Path


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

app = Flask(__name__)
csrf = CSRFProtect(app)


app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = environ["USER_DATABASE_URL"]
app.config['STRIPE_PUBLIC_KEY'] = environ.get('STRIPE_PUBLIC_KEY', '')
app.config.update(
    CATALOGUE_SERVICE_URL=environ.get('CATALOGUE_SERVICE_URL', 'http://localhost:5004'),
    VENUE_SERVICE_URL=environ.get('VENUE_SERVICE_URL', 'http://localhost:5003'),
    CART_SERVICE_URL=environ.get('CART_SERVICE_URL', 'http://localhost:5005'),
    REVIEW_SERVICE_URL=environ.get('REVIEW_SERVICE_URL', 'http://localhost:5007'),
    PROCESS_REVIEW_SERVICE_URL=environ.get('PROCESS_REVIEW_SERVICE_URL', 'http://localhost:5400'),
    VIEW_ORDER_SERVICE_URL=environ.get('VIEW_ORDER_SERVICE_URL', 'http://localhost:5300'),
    PROCESS_ORDER_SERVICE_URL=environ.get('PROCESS_ORDER_SERVICE_URL', 'http://localhost:5200'),
    REFUND_SERVICE_URL=environ.get('REFUND_SERVICE_URL', 'http://localhost:5700'),
)


@app.context_processor
def inject_service_urls():
    return {
        'process_order_url': app.config['PROCESS_ORDER_SERVICE_URL'],
        'refund_service_url': app.config['REFUND_SERVICE_URL'],
    }

db = SQLAlchemy(app)  # database instance
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

login_manager.login_view = 'login'  # Function name of route
login_manager.login_message_category = 'info'

from user_application import routes
