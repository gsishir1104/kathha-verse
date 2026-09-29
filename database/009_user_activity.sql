CREATE TABLE IF NOT EXISTS user_presence (
 user_id VARCHAR(36) PRIMARY KEY REFERENCES users(id),
 first_seen DOUBLE PRECISION NOT NULL,
 last_active DOUBLE PRECISION NOT NULL,
 last_login DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS user_activity (
 id VARCHAR(36) PRIMARY KEY,
 user_id VARCHAR(36) NOT NULL REFERENCES users(id),
 action VARCHAR(100) NOT NULL,
 resource VARCHAR(100) NOT NULL DEFAULT '',
 created DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS ix_user_activity_created ON user_activity(created);
