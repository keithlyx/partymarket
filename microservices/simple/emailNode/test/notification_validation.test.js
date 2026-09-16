const assert = require('node:assert/strict');
const test = require('node:test');

const { validateMessage } = require('../src/notification_validation');


test('rejects unsupported email event types', () => {
  assert.equal(validateMessage({ type: 'password_reset' }), 'Email event has an unsupported type.');
});

test('rejects events without a recipient or order ID', () => {
  assert.equal(
    validateMessage({ type: 'order_refund', user_id: '', order_id: 'ch_123' }),
    'Email event is missing a recipient or order ID.',
  );
});

test('rejects malformed order confirmation items', () => {
  assert.equal(
    validateMessage({
      type: 'order_confirmation',
      user_id: 'user@example.com',
      order_id: 'ch_123',
      order_items: [null],
      total_amount: '12.34',
    }),
    'Order confirmation event is missing order details.',
  );
});

test('accepts a valid refund event', () => {
  assert.equal(validateMessage({
    type: 'order_refund',
    user_id: 'user@example.com',
    order_id: 'ch_123',
  }), null);
});
