# Party Planning Market

Party Planning Market is an event-booking platform where users can browse party items and venues, manage a cart, place orders, view order status, request refunds, and submit reviews.

The platform uses Flask domain services, workflow services, RabbitMQ, Stripe, SendGrid, MySQL, and Docker Compose. The project started as a university microservices project and has since been revisited with stronger API, validation, database, and error-handling practices.

## Architecture

```text
Flask web application
        |
        +--> Simple domain services --> MySQL schemas
        |
        +--> Complex workflow services --> Simple domain services

Order and refund events --> RabbitMQ --> Notification service --> SendGrid
Payment and refund requests --> Stripe
```

The Compose setup uses one MySQL server with separate logical schemas for catalogue, cart, orders, reviews, venue, and users. Each service receives its own database URL and owns only its schema. This keeps the local setup practical while preserving service data ownership.

## Project Structure

- `main/` - Flask web application
- `microservices/simple/` - catalogue, venue, cart, order, review, payment, and notification services
- `microservices/complex/` - order, refund, review, and order-view workflows
- `databases/` - MySQL schema initialization scripts
- `tests/` - focused service and orchestration tests

## Running Locally

1. Copy `.env.example` to `.env`.
2. Set a local `MYSQL_ROOT_PASSWORD` and provide Stripe and SendGrid test credentials if payment or email flows are being exercised.
3. Start the services:

```bash
docker compose up --build
```

The MySQL container initializes the six schemas from `databases/` on its first startup. To re-run initialization from scratch, stop Compose and remove the `mysql_data` volume first. Do not use production credentials in local `.env` files.

The web application is not included as a Compose service and can be run separately after the backend services are available:

```bash
cd main
pip install -r requirements.txt
python app.py
```

When running the web application outside Docker, set `USER_DATABASE_URL` to the host-accessible users schema URL from `.env`.

## API Overview

Backend services use resource-oriented `/api/v1` endpoints:

- `GET /catalogue` and `GET /catalogue/<item_id>` - catalogue data
- `PATCH /catalogue/<item_id>/rating` - catalogue rating update
- `GET /venues` and `GET /venues/<venue_id>` - venue data
- `PATCH /venues/<venue_id>/rating` - venue rating update
- `GET /carts/<user_id>` - retrieve a cart
- `POST /carts/<user_id>/products/<product_id>` - add a cart product
- `PATCH /carts/<user_id>/items/<item_id>` - set item quantity
- `DELETE /carts/<user_id>/products/<product_id>` - remove a cart product
- `DELETE /carts/<user_id>` - clear a cart
- `GET /orders?user_id=<user_id>` and `GET /orders/<order_id>` - order data
- `POST /orders` - create an order through the order workflow
- `PATCH /orders/<order_id>` - update order status
- `GET /reviews?product_id=<product_id>` or `GET /reviews?user_id=<user_id>` - review data
- `POST /reviews` and `PATCH /reviews/<user_id>/<product_id>` - create or edit reviews
- `POST /payments` - create a Stripe payment
- `POST /refunds` - process a Stripe refund

Money is stored in MySQL as `DECIMAL(10,2)` and sent to Stripe as integer cents. API responses represent monetary values as two-decimal strings to avoid floating-point ambiguity.

## Testing

The tests use in-memory SQLite fixtures only to isolate service behavior. Production and Compose configuration require MySQL URLs.

```bash
python -m pytest -q
python -m compileall -q main microservices
docker compose config --quiet
```

Stripe, RabbitMQ, SendGrid, and MySQL integration tests require the corresponding local services or test credentials. The unit tests mock external payment, messaging, and HTTP boundaries where appropriate.
