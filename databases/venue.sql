CREATE schema IF NOT EXISTS venue;

USE venue;

DROP TABLE IF EXISTS venue;
CREATE TABLE IF NOT EXISTS venue (
  venue_id VARCHAR(50) PRIMARY KEY,
  venue_name VARCHAR(100) NOT NULL,
  venue_img VARCHAR(1000) NOT NULL,
  venue_description VARCHAR(1000) NOT NULL,
  venue_price DECIMAL(10, 2) NOT NULL,
  venue_rating FLOAT,
  review_count INT NOT NULL,
  address VARCHAR(255) NOT NULL
);

INSERT INTO venue (venue_id ,venue_name ,venue_img ,venue_description ,venue_price ,venue_rating ,
review_count,address) VALUES('v00','Holiday Inn','Hoiday Inn','Holiday Inn',0.00, 0, 0, '1.2975,103.8494'),
('v02','Gardens by the Bay','Gardens by the Bay','Gardens by the Bay',0.00, 0, 0, '1.2816,103.8636'),
('v03','Sentosa','Sentosa','Sentosa',0.00, 0, 0, '1.2494,103.8303'),
('v04','Tanjong Beach Walk Sentosa','Tanjong Beach Walk Sentosa','Tanjong Beach Walk Sentosa',0.00, 0, 0, '1.2543,103.8238'),
('v05','Merlion Park','Merlion Park','Merlion Park',0.00, 0, 0, '1.2867,103.8546'),
('v06','Marina Bay Sands','Marina Bay Sands','Marina Bay Sands',0.00, 0, 0, '1.2823,103.8585'),
('v07','Singapore Flyer','Singapore Flyer','Singapore Flyer',0.00, 0, 0, '1.2894,103.8635'),
('v08','Botanic Gardens','Botanic Gardens','Botanic Gardens',0.00, 0, 0, '1.3138,103.8156');

