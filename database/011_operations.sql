
CREATE TABLE IF NOT EXISTS support_cases (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	category VARCHAR(30) NOT NULL, 
	subject VARCHAR(160) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	assigned_to VARCHAR(36), 
	created FLOAT NOT NULL, 
	updated FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(assigned_to) REFERENCES users (id)
)

;


CREATE TABLE IF NOT EXISTS case_replies (
	id VARCHAR(36) NOT NULL, 
	case_id VARCHAR(36) NOT NULL, 
	author_id VARCHAR(36) NOT NULL, 
	body TEXT NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES support_cases (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
)

;


CREATE TABLE IF NOT EXISTS operation_events (
	id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36), 
	action VARCHAR(120) NOT NULL, 
	target VARCHAR(160) NOT NULL, 
	reason TEXT NOT NULL, 
	result VARCHAR(30) NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;

CREATE INDEX IF NOT EXISTS ix_operation_events_created ON operation_events (created);


CREATE TABLE IF NOT EXISTS operation_settings (
	key VARCHAR(50) NOT NULL, 
	value JSON NOT NULL, 
	PRIMARY KEY (key)
)

;


CREATE TABLE IF NOT EXISTS ai_jobs (
	id VARCHAR(36) NOT NULL, 
	feature VARCHAR(100) NOT NULL, 
	model VARCHAR(100) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	started FLOAT NOT NULL, 
	ended FLOAT, 
	input_tokens INTEGER, 
	output_tokens INTEGER, 
	PRIMARY KEY (id)
)

;