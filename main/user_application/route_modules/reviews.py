from flask import abort, flash, redirect, request, url_for
from flask_login import current_user, login_required

from user_application import app
from user_application.invokes import invoke_http
from .common import PROCESS_REVIEW_URL


@app.route('/add-review/<prod_id>', methods=['POST'])
@login_required
def add_review(prod_id):
    review_data = {
        "rating": int(request.form['rating']),
        "rating_desc": request.form['review'],
        "user_id": current_user.user_id_email,
        "prod_id": prod_id,
    }
    response = invoke_http(
        PROCESS_REVIEW_URL + '/api/v1/reviews',
        method='POST',
        json=review_data,
    )
    if response.get('code') in range(200, 300):
        flash('Your review has been added!', 'success')

    if prod_id.startswith("i"):
        return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
    if prod_id.startswith("v"):
        return redirect(url_for('venue_detail', venue_id=prod_id))
    return redirect(url_for('home'))


@app.route('/review/edit_review/<user_id>/<prod_id>', methods=['POST'])
@login_required
def update_review(user_id, prod_id):
    if user_id != current_user.user_id_email:
        abort(403)

    review_data = {
        "prod_id": prod_id,
        "user_id": user_id,
        "rating": int(request.form["rating"]),
        "rating_desc": request.form["review"],
    }
    invoke_http(
        PROCESS_REVIEW_URL + "/api/v1/reviews/" + user_id + "/" + prod_id,
        method="PATCH",
        json=review_data,
    )

    if prod_id.startswith("i"):
        return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
    return redirect(url_for('venue_detail', venue_id=prod_id))
