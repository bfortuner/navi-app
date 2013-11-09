use problemlib;

DROP TABLE IF EXISTS users;
CREATE TABLE users (
       user_id INT NOT NULL AUTO_INCREMENT,
       username VARCHAR(128) NOT NULL DEFAULT "Anonymous",
       password VARCHAR(128) NOT NULL,
       about_me TEXT NOT NULL,
       profile_pic CHAR(0),
       email VARCHAR(128),
       PRIMARY KEY (user_id)
);


DROP TABLE IF EXISTS userSubs;
CREATE TABLE userSubs (
       user_id INT(8) DEFAULT 1,
       problem_id INT(8),
       userAnswer TEXT,
       user_status VARCHAR(10) DEFAULT NULL
);


DROP TABLE IF EXISTS problems;
CREATE TABLE problems (
problem_id INT AUTO_INCREMENT
, title VARCHAR(200)
, description TEXT(2000)
, func_name VARCHAR(300)
, solution TEXT(2000)
, tests TEXT(2000)
, category VARCHAR(25) DEFAULT 'Other'
, difficulty INT(1) DEFAULT 3
, author_id INT(8) NOT NULL DEFAULT 1
, PRIMARY KEY (problem_id)
);


/*
INSERT INTO users (username, password, about_me, profile_pic, email)
       VALUES ('bfortuner','aobort90','this is brendans bio', '', 'bfortuner@gmail.com');

INSERT INTO users (username, password, about_me, profile_pic, email)
       VALUES ('cfortuner','colin','this is colins bio', NULL, 'cfortuner@gmail.com');
*/