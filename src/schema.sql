-- Postgres 9.1 or higher required.
CREATE SCHEMA media;

CREATE TABLE IF NOT EXISTS media.mediafile_data (
    id int PRIMARY KEY,
    data bytea,
    mimetype varchar(255)
);

CREATE TABLE IF NOT EXISTS media.resource_data (
    id int PRIMARY KEY,
    data bytea,
    mimetype varchar(255)
);
