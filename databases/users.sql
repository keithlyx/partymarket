CREATE schema IF NOT EXISTS users;
USE users;

DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS  users (
    user_id_email VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(255),
    password VARCHAR(255)
);

