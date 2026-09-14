from user_application import db, login_manager, app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(str(user_id))


class Users(db.Model, UserMixin):
    user_id_email = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phone = db.Column(db.String(60), nullable=True)
    role = db.Column(db.String(20), nullable=True, default="user")

    def get_id(self):
          return (self.user_id_email)

    def __repr__(self):
        return f"Users('{self.username}', '{self.email}')"


with app.app_context():
  # call your method here
    db.create_all()
