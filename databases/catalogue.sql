CREATE schema IF NOT EXISTS catalogue;

USE catalogue;

DROP TABLE IF EXISTS catalogue;
CREATE TABLE IF NOT EXISTS catalogue (
  item_id VARCHAR(10) PRIMARY KEY,
  category_name VARCHAR(100) NOT NULL,
  item_name VARCHAR(255) NOT NULL,
  item_price FLOAT NOT NULL,
  item_img VARCHAR(1000) NOT NULL,
  item_description VARCHAR(1000) NOT NULL,
  item_rating FLOAT NOT NULL,
  review_count INT NOT NULL
);

INSERT INTO catalogue (item_id, category_name, item_name, item_price, item_img, item_description, item_rating, review_count) 
VALUES
('i01', 'Food', 'Chicken Rice', 5.00, 'chicken rice' , 'Delicious chicken rice from airport road' , 0.00 , 0),
('i02', 'Food', 'Fishball Noodle', 4.00, 'fishball noodle' , 'Delicious fishball noodle from airport road' , 0.00 , 0),
('i03', 'Food', 'Rojak', 4.00, 'rojak' , 'Delicious rojak from airport road' , 0.00 , 0),
('i04', 'Food', 'Mr Coconut', 4.00, 'Mr Coconut' , 'Delicious Mr Coconut from airport road' , 0.00 , 0),
('i05', 'Food', 'Duck Rice', 4.00, 'Duck Rice' , 'Delicious Duck Rice from airport road' , 0.00 , 0);