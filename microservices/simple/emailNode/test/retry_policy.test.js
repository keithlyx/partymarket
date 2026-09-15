const assert = require('node:assert/strict');
const test = require('node:test');

const { nextRetryCount } = require('../src/retry_policy');


test('increments retry count below the configured limit', () => {
  assert.equal(nextRetryCount({ 'x-retry-count': 1 }, 3), 2);
});

test('starts retry count at one for a new message', () => {
  assert.equal(nextRetryCount({}, 3), 1);
});

test('stops retrying after the configured limit', () => {
  assert.equal(nextRetryCount({ 'x-retry-count': 3 }, 3), null);
});

test('rejects malformed retry counts', () => {
  assert.equal(nextRetryCount({ 'x-retry-count': 'not-a-number' }, 3), null);
});
