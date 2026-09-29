-- Durable welcome-email queue; one record per new account.

CREATE TABLE IF NOT EXISTS welcome_emails (
	user_id VARCHAR(36) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	attempts INTEGER NOT NULL, 
	next_attempt FLOAT NOT NULL, 
	last_error VARCHAR(80) NOT NULL, 
	sent_at FLOAT, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;
