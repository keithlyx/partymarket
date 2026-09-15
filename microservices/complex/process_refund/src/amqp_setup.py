from os import environ

import pika


hostname = environ.get("rabbit_host") or environ.get("rabbit-host") or "rabbitmq"
port = int(environ.get("rabbit_port", 5672))
exchangename = "email_exchange"
exchangetype = "topic"
queue_name = "email_queue"
connection = None
channel = None


def check_setup():
    global connection, channel

    if connection is None or connection.is_closed:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=hostname,
                port=port,
                heartbeat=3600,
                blocked_connection_timeout=3600,
            )
        )

    if channel is None or channel.is_closed:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=exchangename,
            exchange_type=exchangetype,
            durable=True,
        )
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(
            exchange=exchangename,
            queue=queue_name,
            routing_key="*.email",
        )
