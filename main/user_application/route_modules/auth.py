from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user

from user_application import app, bcrypt, db
from user_application.forms import LoginForm, RegistrationForm, normalize_username
from user_application.models import Users


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Users(
            user_id_email=form.email.data.lower(),
            name=normalize_username(form.username.data),
            password=hashed_password,
        )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to login', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title="Register", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(name=normalize_username(form.username.data)).first()
        if user and user.role in ("admin", "user") and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        flash("Login unsuccessful. Please check email and password.", "danger")

    return render_template('login.html', title="Login", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
