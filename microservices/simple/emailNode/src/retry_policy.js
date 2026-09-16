function nextRetryCount(headers, maxRetries) {
  const currentCount = Number(headers && headers['x-retry-count'] ? headers['x-retry-count'] : 0);
  if (!Number.isInteger(currentCount) || currentCount < 0 || currentCount >= maxRetries) {
    return null;
  }
  return currentCount + 1;
}


module.exports = { nextRetryCount };
