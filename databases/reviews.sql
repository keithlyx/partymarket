CREATE schema IF NOT EXISTS reviews;

USE reviews;


DROP TABLE IF EXISTS reviews;
CREATE TABLE IF NOT EXISTS  reviews (
  user_id VARCHAR(100) NOT NULL,
  item_venue_id VARCHAR(8) NOT NULL,
  rating INT,
  rating_desc VARCHAR(255),
  PRIMARY KEY (user_id, item_venue_id)
);

