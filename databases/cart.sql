CREATE schema IF NOT EXISTS cart;

USE cart;

DROP TABLE IF EXISTS cart_item;
CREATE TABLE IF NOT EXISTS cart_item (
user_id VARCHAR(100),
item_id INT,
item_quantity INT,
PRIMARY KEY (user_id, item_id)
);

DROP TABLE IF EXISTS cart_venue;
CREATE TABLE IF NOT EXISTS  cart_venue (
user_id VARCHAR(100),
venue_id INT,
venue_datetime DATETIME,
PRIMARY KEY (user_id, venue_id)
);


