CREATE TABLE IF NOT EXISTS notifications (
 id VARCHAR(36) PRIMARY KEY,
 sender_id VARCHAR(36) NOT NULL REFERENCES users(id),
 user_id VARCHAR(36) NOT NULL REFERENCES users(id),
 title VARCHAR(160) NOT NULL,
 body TEXT NOT NULL,
 created DOUBLE PRECISION NOT NULL,
 read_at DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id);
