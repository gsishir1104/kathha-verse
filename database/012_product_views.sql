
CREATE TABLE publications (
	chapter_id VARCHAR(36) NOT NULL, 
	snapshot_id VARCHAR(36) NOT NULL, 
	active INTEGER NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (chapter_id), 
	FOREIGN KEY(chapter_id) REFERENCES chapters (id), 
	FOREIGN KEY(snapshot_id) REFERENCES snapshots (id)
)

;


CREATE TABLE public_reading (
	key VARCHAR(80) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	snapshot_id VARCHAR(36) NOT NULL, 
	data JSON NOT NULL, 
	PRIMARY KEY (key), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(snapshot_id) REFERENCES snapshots (id)
)

;


CREATE TABLE incident_states (
	key VARCHAR(80) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	reason VARCHAR(1000) NOT NULL, 
	PRIMARY KEY (key)
)

;


CREATE TABLE public_discussions (
	id VARCHAR(36) NOT NULL, 
	snapshot_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	body VARCHAR(2000) NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(snapshot_id) REFERENCES snapshots (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;