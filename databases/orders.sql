CREATE schema IF NOT EXISTS orders;

USE orders;

DROP TABLE IF EXISTS order_venue;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
CREATE TABLE IF NOT EXISTS orders (
  order_id VARCHAR(100) NOT NULL PRIMARY KEY,
  user_id VARCHAR(100) NOT NULL,
  total_amount DECIMAL(10, 2) NOT NULL,
  order_datetime VARCHAR(255) NOT NULL,
  delivery_address VARCHAR(255) NOT NULL,
  delivery_datetime VARCHAR(255) NOT NULL,
  order_status VARCHAR(100) NOT NULL
);

DROP TABLE IF EXISTS order_items;
CREATE TABLE IF NOT EXISTS order_items (
  order_id VARCHAR(100) NOT NULL ,
  item_id VARCHAR(255) NOT NULL,
  item_quantity INT NOT NULL,
  item_price DECIMAL(10, 2) NOT NULL,
  PRIMARY KEY (order_id, item_id),
  FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

DROP TABLE IF EXISTS order_venue;
CREATE TABLE IF NOT EXISTS order_venue (
  order_id VARCHAR(100) NOT NULL,
  venue_id VARCHAR(255) NOT NULL,
  venue_price DECIMAL(10, 2) NOT NULL,
  venue_datetime VARCHAR(255) NOT NULL,
  PRIMARY KEY (order_id, venue_id),
  FOREIGN KEY (order_id) REFERENCES orders (order_id)
);


