import pika
from os import environ
# These module-level variables are initialized whenever a new instance of python interpreter imports the module;
# In each instance of python interpreter (i.e., a program run), the same module is only imported once (guaranteed by the interpreter).

hostname = environ.get('rabbit-host') or "rabbitmq" # default hostname
port = 5672 # default port
# connect to the broker and set up a communication channel in the connection
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=hostname, port=port,
        heartbeat=3600, blocked_connection_timeout=3600, # these parameters to prolong the expiration time (in seconds) of the connection
))
    # Note about AMQP connection: various network firewalls, filters, gateways (e.g., SMU VPN on wifi), may hinder the connections;
    # If "pika.exceptions.AMQPConnectionError" happens, may try again after disconnecting the wifi and/or disabling firewalls.
    # If see: Stream connection lost: ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None)
    # - Try: simply re-run the program or refresh the page.
    # For rare cases, it's incompatibility between RabbitMQ and the machine running it,
    # - Use the Docker version of RabbitMQ instead: https://www.rabbitmq.com/download.html
channel = connection.channel()
# Set up the exchange if the exchange doesn't exist
# - use a 'topic' exchange to enable interaction
exchangename="process_order"
exchangetype="topic"
channel.exchange_declare(exchange=exchangename, exchange_type=exchangetype, durable=True)
    # 'durable' makes the exchange survive broker restarts

# Here can be a place to set up all queues needed by the microservices,
# - instead of setting up the queues using RabbitMQ UI.

############   Notification queue   #############
#delcare Notification queue
queue_name = 'Notification'
channel.queue_declare(queue=queue_name, durable=True) 
    # 'durable' makes the queue survive broker restarts

#bind Notification queue
channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='*.email')
    # bind the queue to the exchange via the key
    # any routing_key with two words and ending with '.email' will be matched

############   Order_Log queue    #############
#delcare Order_Log queue
queue_name = 'Order_Log'
channel.queue_declare(queue=queue_name, durable=True)
    # 'durable' makes the queue survive broker restarts

#bind Order_Log queue
channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='*.order')
    # bind the queue to the exchange via the key
    # 'routing_key=#' => any routing_key would be matched


############  Payment queue    #############
#delcare Payment
queue_name = 'Payment'
channel.queue_declare(queue=queue_name, durable=True)
    # 'durable' makes the queue survive broker restarts

#bind Payment queue
channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='*.payment')
    # bind the queue to the exchange via the key
    # 'routing_key=#' => any routing_key would be matched


# exchangename="payment"
# exchangetype="topic"
# channel.exchange_declare(exchange=exchangename, exchange_type=exchangetype, durable=True)
#     # 'durable' makes the exchange survive broker restarts
#
# ############   Process_Order queue   #############
# #delcare process_order queue
# queue_name = 'process_order'
# channel.queue_declare(queue=queue_name, durable=True)
#     # 'durable' makes the queue survive broker restarts
#
# #bind process_order queue
# channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='*.process_order')
#     # bind the queue to the exchange via the key
#     # any routing_key with two words and ending with '.process_order' will be matched

"""
This function in this module sets up a connection and a channel to a local AMQP broker,
and declares a 'topic' exchange to be used by the microservices in the solution.
"""
def check_setup():
    # The shared connection and channel created when the module is imported may be expired, 
    # timed out, disconnected by the broker or a client;
    # - re-establish the connection/channel is they have been closed
    global connection, channel, hostname, port, exchangename, exchangetype

    if not is_connection_open(connection):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port, heartbeat=3600, blocked_connection_timeout=3600))
    if channel.is_closed:
        channel = connection.channel()
        channel.exchange_declare(exchange=exchangename, exchange_type=exchangetype, durable=True)


def is_connection_open(connection):
    # For a BlockingConnection in AMQP clients,
    # when an exception happens when an action is performed,
    # it likely indicates a broken connection.
    # So, the code below actively calls a method in the 'connection' to check if an exception happens
    try:
        connection.process_data_events()
        return True
    except pika.exceptions.AMQPError as e:
        print("AMQP Error:", e)
        print("...creating a new connection.")
        return False
