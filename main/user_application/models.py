from user_application import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(str(user_id))


class Users(db.Model, UserMixin):
    __tablename__ = "users"

    user_id_email = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=True, default="user")

    def get_id(self):
        return self.user_id_email

    def __repr__(self):
        return f"Users('{self.name}', '{self.user_id_email}')"
