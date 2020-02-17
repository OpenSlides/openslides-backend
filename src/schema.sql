-- Postgres 9.1 or higher required.
CREATE TABLE IF NOT EXISTS mediafile_data (
    id int PRIMARY KEY,
    data bytea,
    mimetype varchar(255)
);
