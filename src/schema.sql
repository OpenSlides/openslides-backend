-- Postgres 9.1 or higher required.
CREATE SCHEMA IF NOT EXISTS media;

CREATE TABLE IF NOT EXISTS media.mediafile_data (
    id int PRIMARY KEY,
    data bytea,
    mimetype varchar(255)
);
