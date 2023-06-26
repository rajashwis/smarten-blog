--dropping tables if they exist. always drop the child table first
DROP TABLE IF EXISTS post_tags CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS article CASCADE;
DROP TABLE IF EXISTS users;

--creating an ARTICLE table
CREATE TABLE article (
	article_id INT GENERATED ALWAYS AS IDENTITY,
    title TEXT,
    content_ TEXT,
    summary TEXT,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    image_path VARCHAR(255),
    author_no INT NOT NULL,
    PRIMARY KEY (article_id)
	CONSTRAINT fk_user 
    	FOREIGN KEY (author_no) 
			REFERENCES users(user_id),
	
);

--creating a TAGS table
CREATE TABLE tags (
	tag_id INT GENERATED ALWAYS AS IDENTITY,
    tag_name VARCHAR(80),
    PRIMARY KEY (tag_id)
);

--creating a POST_TAGS table
CREATE TABLE post_tags (
	tag_no INT NOT NULL,
    article_no INT NOT NULL,
	CONSTRAINT fk_tag
    	FOREIGN KEY (tag_no) 
			REFERENCES tags(tag_id),
	CONSTRAINT fk_article
    	FOREIGN KEY (article_no) 
			REFERENCES article(article_id),
    PRIMARY KEY (tag_no, article_no)
);