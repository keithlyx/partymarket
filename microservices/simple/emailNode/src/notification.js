
const path = require('path');
const sgMail = require('@sendgrid/mail');
const amqp_setup = require('./amqp_setup');
const process = require('process');
const monitorBindingKey = '*.email';
const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY;

async function receiveConfirmation() {
  try {
    const channel = await amqp_setup.checkSetup();
    const queueName = 'email_queue';

    console.log(`[*] Waiting for messages in ${queueName}. To exit press CTRL+C`);
    await channel.consume(queueName, async (msg) => {
      if (!msg) {
        return;
      }

      try {
        const shouldAcknowledge = await callback(msg);
        if (shouldAcknowledge) {
          channel.ack(msg);
        } else {
          channel.nack(msg, false, false);
        }
      } catch (err) {
        console.error('Email delivery failed; message will be retried:', err.message);
        channel.nack(msg, false, true);
      }
    }, { noAck: false });
  } catch (err) {
    console.error('Error starting email consumer:', err.message);
    process.exitCode = 1;
  }
}


// required signature for the callback; no return
async function callback(msg) {
  let jsonMsg;
  try {
    jsonMsg = JSON.parse(msg.content.toString());
  } catch (err) {
    processError('Email message was not valid JSON.');
    return false;
  }

  await mail(jsonMsg);
  return true;
}
function processError(errorMsg) {
  console.error(errorMsg);
}

async function mail(jsonMsg) {
  // email address, subject and body
  
  const emailContent = format_email(jsonMsg);

  const sub = jsonMsg.type;

  const message = {
    to: jsonMsg['user_id'],
    from: 'partypoopersSMU@gmail.com',
    subject: sub,
    html: emailContent,
  };

  // sending email and printing status
  try {
    sgMail.setApiKey(SENDGRID_API_KEY);
    await sgMail.send(message);
  } catch (err) {
    throw new Error(`SendGrid delivery failed: ${err.message}`);
  }
}

if (require.main === module) {
  console.log(`\nThis is ${path.basename(__filename)}: monitoring routing key '${monitorBindingKey}' in exchange ...`);
  receiveConfirmation();
  
}

function format_email(data) {
  const sub = data.type;
  if (sub === "order_refund") {
    
    return `
          <!DOCTYPE html>
          <html lang="en">
          <head>
            <meta charset="UTF-8">
            <title>Order Refund</title>
            <style>
              body {
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #333;
              }
              .container {
                max-width: 600px;
                margin: 0 auto;
              }
              h1 {
                font-size: 28px;
                margin-top: 30px;
                margin-bottom: 0;
                text-align: center;
              }
              .details {
                border-collapse: collapse;
                margin-top: 30px;
                width: 100%;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <h1>Order Refund'</h1>
              <p>Dear ${data.user_id},</p>
              <p>Your order #${data.order_id}'s has been cancelled.</p>
              <p>Your refund has been processed and will be credited to your account soon.</p>
            </div>
          </body>
          </html>`
  } else if (sub === "order_confirmation") {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Order Notification</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          font-size: 14px;
          color: #333;
        }
        .container {
          max-width: 600px;
          margin: 0 auto;
        }
        
        h1 {
          font-size: 28px;
          margin-top: 30px;
          margin-bottom: 0;
          text-align: center;
        }
        
        .details {
          border-collapse: collapse;
          margin-top: 30px;
          width: 100%;
        }
        
        .details th, .details td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        
        .details th {
          background-color: #f2f2f2;
        }
        
        .total {
          text-align: right;
        }
        
        .footer {
          margin-top: 30px;
          text-align: center;
        }
        
        .footer p {
          margin: 0;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Order Notification</h1>
        <p>Dear ${data.username},</p>
        <p>Thank you for placing an order with us. Below are the details of your order #${data.order_id}:</p>
        <table class="details">
          <thead>
            <tr>
              <th>Item Name</th>
              <th>Price</th>
              <th>Quantity</th>
            </tr>
          </thead>
          <tbody>
            ${data.order_items.map(item => `<tr><td>${item.item_name}</td><td>$${item.item_price}</td><td>${item.item_quantity}</td></tr>`).join('')}
            ${data.venue ? `
            <tr>
              <th>Venue</th>
              <th>Price</th>
              <th>Booking Details</th>
            </tr>
            <tr>
              <td>${data.venue.venue_name}</td>
              <td>$${data.venue.venue_price}</td>
              <td>${data.venue.venue_datetime}</td>
            </tr>` : ''}
          </tbody>
          <tfoot>
            <tr>
              <td colspan="2" class="total">Total:</td>
              <td>$${data.total_amount}</td>
            </tr>
          </tfoot>
        </table>
        <p>Thank you for your business.</p>
      </div>
    </body>
    </html>`;
    return output
  }

}
