# Party Planning Market

Party Planning Market is event-booking platform where users can browse party items and venues, manage a cart, place orders, view order status, request refunds, and submit reviews.

The platform uses Flask domain services, workflow services, RabbitMQ, Stripe, SendGrid, MySQL, and Docker Compose. This repository is a maintained public copy; the current branch adds versioned APIs, environment-based configuration, validation, focused tests, and safer payment and notification handling while keeping the project’s overall scope intact.

## Architecture
![System architecture](resources/architecture.png)



### Scenarios
Scenario 1: submit an order
![Submit order workflow](resources/SubmitOrder.png)
Scenario 2: View Order 
![Review workflow](resources/Review1.png)
Scenario 2: Cancel an order
![Cancellation workflow](resources/Cancellation.png)



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

local services or test credentials. The unit tests mock external payment, messaging, and HTTP boundaries where appropriate.
