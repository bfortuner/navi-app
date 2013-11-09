use navi;

DROP TABLE IF EXISTS users;
CREATE TABLE users (
       user_id INT NOT NULL AUTO_INCREMENT,
       full_name VARCHAR(128) NOT NULL DEFAULT "R. Daneel Olivaw",
       password VARCHAR(128) NOT NULL,
       about_me TEXT NOT NULL,
       profile_pic CHAR(0),
       email VARCHAR(128),
       PRIMARY KEY (user_id)
);


DROP TABLE IF EXISTS categories;
CREATE TABLE categories (
       category_id INT AUTO_INCREMENT
       , title VARCHAR(200)
       , description TEXT(500)	
       , subcategories VARCHAR(500)
       , PRIMARY KEY (category_id)
);

DROP TABLE IF EXISTS userRatings;
CREATE TABLE userRatings (
       link_id INT
       , user_id INT
       , rating INT(1)
);

DROP TABLE IF EXISTS links;
CREATE TABLE links (
link_id INT AUTO_INCREMENT
, title VARCHAR(200)
, description TEXT(500)
, url VARCHAR(300)
, category VARCHAR(25) DEFAULT 'Other'
, rating_sum INT(6) DEFAULT 10
, rating_votes INT(6) DEFAULT 10
, author_id INT NOT NULL DEFAULT 1
, PRIMARY KEY (link_id)
);


/*
INSERT INTO users (username, password, about_me, profile_pic, email)
       VALUES ('bfortuner','aobort90','this is brendans bio', '', 'bfortuner@gmail.com');

INSERT INTO users (username, password, about_me, profile_pic, email)
       VALUES ('cfortuner','colin','this is colins bio', NULL, 'cfortuner@gmail.com');
*/