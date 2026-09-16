const SUPPORTED_EVENT_TYPES = ['order_confirmation', 'order_refund'];

function isNonEmptyString(value) {
  return typeof value === 'string' && Boolean(value.trim());
}

function hasOrderDetails(data) {
  return Array.isArray(data.order_items)
    && data.order_items.every(item => item && typeof item === 'object')
    && data.total_amount !== undefined;
}

function validateMessage(data) {
  if (!data || typeof data !== 'object' || !SUPPORTED_EVENT_TYPES.includes(data.type)) {
    return 'Email event has an unsupported type.';
  }
  if (!isNonEmptyString(data.user_id) || !isNonEmptyString(data.order_id)) {
    return 'Email event is missing a recipient or order ID.';
  }
  if (data.type === 'order_confirmation' && !hasOrderDetails(data)) {
    return 'Order confirmation event is missing order details.';
  }
  return null;
}

module.exports = { isNonEmptyString, validateMessage };
