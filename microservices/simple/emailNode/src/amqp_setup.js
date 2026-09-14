const amqp = require('amqplib');

// These variables can be set based on the AMQP broker being used
const hostname = "rabbitmq";
const port = 5672;
const exchangename = "email_exchange";
const exchangetype = "topic";

// Set up the connection and channel to the AMQP broker
var connection = null;
var channel = null;

amqp.connect(`amqp://${hostname}:${port}`, "heartbeat=60")
    .then((conn) => {
      connection = conn;
      return connection.createChannel();
    })
    .then((ch) => {
      channel = ch;
      // Set up the exchange
      return channel.assertExchange(exchangename, exchangetype, { durable: true });
    })
    .then(() => {
      // Set up the email queue
      const queue_name = 'email_queue';
      return channel.assertQueue(queue_name, { durable: true });
    })
    .then(() => {
      const queue_name = 'email_queue';
      return channel.bindQueue(queue_name, exchangename, '*.email');
    })
    .catch(console.error);

// Check if the connection/channel to the AMQP broker is still open
function isConnectionOpen() {
  if (!connection || !channel) {
    return false;
  }

  return true;
}

// Re-establish the connection/channel if they have been closed
async function checkSetup() {
    let channel = null
    console.log('checkSetup');
    if (!isConnectionOpen()) {

        console.log('reconnecting');
        channel = amqp.connect(`amqp://${hostname}:${port}`, "heartbeat=60")
            .then((conn) => {
                connection = conn;
                channel = connection.createChannel()
                return channel;
            })
}
return channel;

}



module.exports = {
  checkSetup,
  channel
};
