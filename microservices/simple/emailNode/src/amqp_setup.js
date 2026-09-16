const amqp = require('amqplib');

const hostname = process.env.RABBITMQ_HOST || 'rabbitmq';
const port = process.env.RABBITMQ_PORT || 5672;
const exchangeName = 'email_exchange';
const exchangeType = 'topic';
const queueName = 'email_queue';

let connection = null;
let channel = null;
let setupPromise = null;

async function connect() {
  const nextConnection = await amqp.connect(`amqp://${hostname}:${port}`, { heartbeat: 60 });
  nextConnection.on('close', () => {
    connection = null;
    channel = null;
    setupPromise = null;
  });
  nextConnection.on('error', (error) => {
    console.error('RabbitMQ connection error:', error.message);
  });

  const nextChannel = await nextConnection.createChannel();
  await nextChannel.assertExchange(exchangeName, exchangeType, { durable: true });
  await nextChannel.assertQueue(queueName, { durable: true });
  await nextChannel.bindQueue(queueName, exchangeName, '*.email');

  connection = nextConnection;
  channel = nextChannel;
  return channel;
}

async function checkSetup() {
  if (connection && channel) {
    return channel;
  }

  if (!setupPromise) {
    setupPromise = connect().catch((error) => {
      setupPromise = null;
      throw error;
    });
  }

  return setupPromise;
}

module.exports = {
  checkSetup,
  get channel() {
    return channel;
  },
};
