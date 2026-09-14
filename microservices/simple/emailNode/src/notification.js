
const path = require('path');
const sgMail = require('@sendgrid/mail');
const amqp_setup = require('./amqp_setup');
const process = require('process');
const monitorBindingKey = '*.email';
const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY;

async function receiveConfirmation() {
  let channel;
  try {
    channel = await amqp_setup.checkSetup();

    setTimeout(() => {
      const queueName = 'email_queue';

      console.log(` [*] Waiting for messages in ${queueName}. To exit press CTRL+C`);

      // set up a consumer and start to wait for coming messages

      channel.consume(queueName, (msg) =>{
              callback(msg)
              channel.ack(msg)
      },
          {noAck: false}
      )

    }, 1000); // 1 seconds delay


    // an implicit loop waiting to receive messages;

    // it doesn't exit by default. Use Ctrl+C in the command window to terminate it.
  } catch (err) {
    console.error('Error in receiveConfirmation:', err);
  }
}


// required signature for the callback; no return
async function callback(msg) {

  console.log(`\nReceived an email request by ${__filename}`);

  try {
    const jsonMsg = JSON.parse(msg.content.toString());
    console.log("checkkk", jsonMsg);
    await mail(jsonMsg);
  } catch (err) {
    processError(msg.content.toString());
  }
}
function processError(errorMsg) {
  console.log('Printing the error message:');
  try {
    const error = JSON.parse(errorMsg);
    console.log('--JSON:', error);
  } catch (err) {
    console.log('--NOT JSON:', err);
    console.log('--DATA:', errorMsg);
  }
  console.log();
}

async function mail(jsonMsg) {
  // email address, subject and body
  
  const emailContent = format_email(jsonMsg);

  const sub = jsonMsg.type;
  console.log(sub);
  console.log(jsonMsg.user_id);

  const message = {
    to: jsonMsg['user_id'],
    from: 'partypoopersSMU@gmail.com',
    subject: sub,
    html: emailContent,
  };

  // sending email and printing status
  try {
    sgMail.setApiKey(SENDGRID_API_KEY);
    const response = await sgMail.send(message);
  } catch (err) {
    console.log(err);
  }
}

if (require.main === module) {
  console.log(`\nThis is ${path.basename(__filename)}: monitoring routing key '${monitorBindingKey}' in exchange ...`);
  receiveConfirmation();
  
}

function format_email(data) {
  const sub = data.type;
  console.log("check email type", sub)
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
    console.log("generating order confirm email")
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
