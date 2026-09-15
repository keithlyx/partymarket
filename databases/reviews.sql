CREATE schema IF NOT EXISTS reviews;

USE reviews;


DROP TABLE IF EXISTS review_items;
CREATE TABLE IF NOT EXISTS review_items (
  user_id VARCHAR(100) NOT NULL,
  prod_id VARCHAR(255) NOT NULL,
  rating INT NOT NULL,
  rating_desc VARCHAR(255) NOT NULL,
  created_date VARCHAR(255) NOT NULL,
  PRIMARY KEY (user_id, prod_id)
);

