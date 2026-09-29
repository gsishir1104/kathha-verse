-- Additive tables for draft recovery and graph feedback.


CREATE TABLE chapter_history (
	id VARCHAR(36) NOT NULL, 
	chapter_id VARCHAR(36) NOT NULL, 
	revision INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	content TEXT NOT NULL, 
	intent JSON NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chapter_id) REFERENCES chapters (id)
)

;


CREATE TABLE graph_comments (
	id VARCHAR(36) NOT NULL, 
	snapshot_id VARCHAR(36) NOT NULL, 
	release_id VARCHAR(36) NOT NULL, 
	reader_id VARCHAR(36) NOT NULL, 
	entity_id VARCHAR(100) NOT NULL, 
	target_id VARCHAR(100) NOT NULL, 
	category VARCHAR(30) NOT NULL, 
	text TEXT NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(snapshot_id) REFERENCES snapshots (id), 
	FOREIGN KEY(release_id) REFERENCES releases (id), 
	FOREIGN KEY(reader_id) REFERENCES users (id)
)

;


CREATE TABLE feedback_states (
	key VARCHAR(80) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	PRIMARY KEY (key)
)

;