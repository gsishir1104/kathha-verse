CREATE TABLE IF NOT EXISTS ai_requests (
 id varchar(36) PRIMARY KEY,
 user_id varchar(36) NOT NULL REFERENCES users(id),
 kind varchar(20) NOT NULL,
 created double precision NOT NULL
);
