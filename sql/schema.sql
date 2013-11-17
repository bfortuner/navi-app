use navi;

DROP TABLE IF EXISTS users;
CREATE TABLE users (
       user_id INT NOT NULL AUTO_INCREMENT,
       username VARCHAR(128) NOT NULL DEFAULT "R. Daneel Olivaw",
       password VARCHAR(128) NOT NULL,
       about_me TEXT NOT NULL,
       profile_pic CHAR(1) DEFAULT 'N',
       email VARCHAR(128),
       join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       tagged_links VARCHAR(5000) DEFAULT '',
       PRIMARY KEY (user_id)
);


DROP TABLE IF EXISTS categories;
CREATE TABLE categories (
       category_id INT AUTO_INCREMENT
       , title VARCHAR(200)
       , description TEXT(500)	
       , subcategories VARCHAR(500) DEFAULT ''
       , PRIMARY KEY (category_id)
);

DROP TABLE IF EXISTS userRatings;
CREATE TABLE userRatings (
       link_id INT
       , user_id INT
       , rating INT(1)
       , tagged CHAR(1) DEFAULT 'N'
);

DROP TABLE IF EXISTS links;
CREATE TABLE links (
link_id INT AUTO_INCREMENT
, title VARCHAR(200)
, description TEXT(500)
, url VARCHAR(300)
, category VARCHAR(25) DEFAULT 'Other'
, content_type VARCHAR(25) DEFAULT 'Article'
, rating_sum INT(6) DEFAULT 4
, rating_votes INT(6) DEFAULT 2
, author_id INT NOT NULL DEFAULT 1
, creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
, PRIMARY KEY (link_id)
);


/*
INSERT INTO users (password, about_me, profile_pic, email)
       VALUES ('aobort90','this is brendans bio', '', 'bfortuner@gmail.com');

*/
INSERT INTO categories (title, description)
       VALUES ('Startups','A startup is an organization formed to search for a repeatable and scalable business model. This section is for the top articles, videos, and books about launching and growing a startup');

/*
INSERT INTO links (title, description, url, content_type, category)
       VALUES ('The Lean Startup by Eric Ries','So youre an ideas guy? Read this and be humbled. The single best book on the market for learning how to launch a startup. A founder who masters these principles will be valuable to any team.', 'https://www.goodreads.com/book/show/10127019-the-lean-startup','Book', 'Startups');

INSERT INTO links (title, description, url, content_type, category)
       VALUES ('Guide To Finding A Technical Co-founder','Vinicius Vacanti, an ex-finance guy turned software entrepreneur, talks about your options as a non-technical founder. His story is inspiring and instructive. A must read.', 'http://www.problem.com','book', 'Startups');

INSERT INTO links (title, description, url, content_type, category)
       VALUES ('A Students Guide To Startups', 'So youve decided that startups are for you? Paul Graham talks about what an aspiring entrepreneur can do to make the most of his college experience.', 'https://www.brendanfortuner.com','book', 'Startups');

*/