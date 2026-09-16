# Party Planning Market

This was a 2023/24 team project. We built an event-booking platform where users can browse party items and venues, manage a cart, place orders, view order status, request refunds, and submit reviews.

The platform uses Flask domain services, workflow services, RabbitMQ, Stripe, SendGrid, MySQL, and Docker Compose. This repository is a maintained public copy; the current branch adds versioned APIs, environment-based configuration, validation, focused tests, and safer payment and notification handling while keeping the project’s overall scope intact.

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

![System architecture](resources/architecture.png)

The web application is the browser-facing entry point. It retrieves cart and catalogue data through the services, calculates order totals on the server, and forwards authenticated checkout and refund requests to the relevant workflows. Service ports are bound to localhost for the local Compose setup.

### Selected workflows

![Submit order workflow](resources/SubmitOrder.png)

![Cancellation workflow](resources/Cancellation.png)

![Review workflow](resources/Review1.png)

The Compose setup uses one MySQL server with separate logical schemas for catalogue, cart, orders, reviews, venue, and users. Each service receives its own database URL and owns only its schema. This keeps the local setup practical while preserving service data ownership.

## Project Structure

- `main/` - Flask web application
- `microservices/simple/` - catalogue, venue, cart, order, review, payment, and notification services
- `microservices/complex/` - order, refund, review, and order-view workflows
- `databases/` - MySQL schema initialization scripts
- `tests/` - focused service and orchestration tests

## Running Locally

1. Copy `.env.example` to `.env`.
2. Set a local `MYSQL_ROOT_PASSWORD` and provide Stripe and SendGrid test credentials if payment or email flows are being exercised. Set `SENDGRID_FROM_EMAIL` to a verified sender if email delivery is enabled.
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

When running the web application outside Docker, set `USER_DATABASE_URL` to the host-accessible users schema URL from `.env`. The web application is intended to be the browser-facing entry point; the other services are local development services and should not be exposed directly to the internet.

## API Overview

All backend service paths begin with `/api/v1`.

The browser-facing web application provides:

- `POST /api/v1/checkout` - submit a payment token and delivery details for the current user’s cart
- `POST /api/v1/refunds` - request a refund for an order owned by the current user

The internal service endpoints include:

- `GET /api/v1/catalogue` and `GET /api/v1/catalogue/<item_id>` - catalogue data
- `PATCH /api/v1/catalogue/<item_id>/rating` - catalogue rating update
- `GET /api/v1/venues` and `GET /api/v1/venues/<venue_id>` - venue data
- `PATCH /api/v1/venues/<venue_id>/rating` - venue rating update
- `GET /api/v1/carts/<user_id>` - retrieve a cart
- `POST /api/v1/carts/<user_id>/products/<product_id>` - add a cart product
- `PATCH /api/v1/carts/<user_id>/items/<item_id>` - set item quantity
- `DELETE /api/v1/carts/<user_id>/products/<product_id>` - remove a cart product
- `DELETE /api/v1/carts/<user_id>` - clear a cart
- `GET /api/v1/orders?user_id=<user_id>` and `GET /api/v1/orders/<order_id>` - order data
- `POST /api/v1/orders` - create an order through the order workflow
- `PATCH /api/v1/orders/<order_id>` - update order status
- `GET /api/v1/reviews?product_id=<product_id>` or `GET /api/v1/reviews?user_id=<user_id>` - review data
- `POST /api/v1/reviews` and `PATCH /api/v1/reviews/<user_id>/<product_id>` - create or edit reviews
- `POST /api/v1/payments` - create a Stripe payment
- `POST /api/v1/refunds` - process a Stripe refund through the payment service

Money is stored in MySQL as `DECIMAL(10,2)` and sent to Stripe as integer cents. API responses represent monetary values as two-decimal strings to avoid floating-point ambiguity.

## Testing

The tests use in-memory SQLite fixtures only to isolate service behavior. Production and Compose configuration require MySQL URLs.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q main microservices
docker compose config --quiet
```

The notification service has its own dependency-free unit tests:

```bash
cd microservices/simple/emailNode
npm install
npm test
```

GitHub Actions runs the Python tests, notification tests, syntax checks, patch-format checks, and Compose configuration validation on pushes and pull requests.

Stripe, RabbitMQ, SendGrid, and MySQL integration tests require the corresponding local services or test credentials. The unit tests mock external payment, messaging, and HTTP boundaries where appropriate.
