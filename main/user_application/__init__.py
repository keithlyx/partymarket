from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from os import environ

app = Flask(__name__)
csrf = CSRFProtect(app)


app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = environ["USER_DATABASE_URL"]
app.config['STRIPE_PUBLIC_KEY'] = environ.get('STRIPE_PUBLIC_KEY', '')

db = SQLAlchemy(app)  # database instance
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

login_manager.login_view = 'login'  # Function name of route
login_manager.login_message_category = 'info'

from user_application import routes
