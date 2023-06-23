#creating the database we're gonna work in
CREATE SCHEMA smarten_blog;

#making sure we're using the required database
use smarten_blog;

#altering our database so that utf-8 encoding is handled properly
ALTER DATABASE smarten_b CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

#dropping tables if they exist. always drop the child table first
DROP TABLE IF EXISTS post_tags CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS article CASCADE;
DROP TABLE IF EXISTS users;

#creating an ARTICLE table
CREATE TABLE article (
	article_id TINYINT AUTO_INCREMENT NOT NULL,
    title TEXT,
    content LONGTEXT,
    summary TEXT,
    created_at DATETIME DEFAULT now(),
    image_path VARCHAR(255),
    author_no INT NOT NULL,
    PRIMARY KEY (article_id),
    FOREIGN KEY (author_no) REFERENCES users(id)
);

#creating a TAGS table
CREATE TABLE tags (
	tag_id TINYINT AUTO_INCREMENT NOT NULL,
    tag_name VARCHAR(80),
    PRIMARY KEY (tag_id)
);

#creating a POST_TAGS table
CREATE TABLE post_tags (
	tag_no TINYINT NOT NULL,
    article_no TINYINT NOT NULL,
    FOREIGN KEY (tag_no) REFERENCES tags(tag_id),
    FOREIGN KEY (article_no) REFERENCES article(article_id),
    PRIMARY KEY (tag_no, article_no)
);
