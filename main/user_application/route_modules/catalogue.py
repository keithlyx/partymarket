from flask import render_template
from flask_login import login_required

from user_application import app
from user_application.invokes import invoke_http
from .common import CATALOGUE_URL, REVIEW_URL, VENUE_URL


def _reviews_for_product(product_id):
    response = invoke_http(
        REVIEW_URL + "/api/v1/reviews",
        method='GET',
        params={"product_id": product_id},
    )
    if not isinstance(response, dict):
        return []
    review_data = response.get('data')
    if not isinstance(review_data, dict):
        return []
    reviews = review_data.get('reviews', [])
    return reviews if isinstance(reviews, list) else []


@app.route('/', methods=['GET'])
def home():
    catalogue_data = invoke_http(CATALOGUE_URL + "/api/v1/catalogue", method='GET')
    venue_data = invoke_http(VENUE_URL + "/api/v1/venues", method='GET')
    return render_template(
        'catalogue.html',
        title="Catalogue",
        catalogue_data=catalogue_data,
        venue_data=venue_data,
    )


@app.route('/catalogue/<catalogue_id>', methods=['GET'])
@login_required
def catalogue_detail(catalogue_id):
    catalogue_data = invoke_http(
        CATALOGUE_URL + "/api/v1/catalogue/" + catalogue_id,
        method='GET',
    )
    return render_template(
        "catalogue-detail.html",
        title="Catalogue Detail",
        catalogue_data=catalogue_data['data'],
        catalogue_review=_reviews_for_product(catalogue_id),
    )


@app.route('/venue/<venue_id>', methods=['GET'])
@login_required
def venue_detail(venue_id):
    venue_data = invoke_http(VENUE_URL + "/api/v1/venues/" + venue_id, method='GET')
    return render_template(
        "venue-detail.html",
        title="Venue Detail",
        venue_data=venue_data['data'],
        venue_review=_reviews_for_product(venue_id),
    )
