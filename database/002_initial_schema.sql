-- Initial application schema for review. Startup create_all applies these tables.

CREATE TABLE users (
	id VARCHAR(36) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	password_hash TEXT NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	preferences JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
)

;


CREATE TABLE sessions (
	token_hash VARCHAR(64) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	expires FLOAT NOT NULL, 
	PRIMARY KEY (token_hash), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;


CREATE TABLE stories (
	id VARCHAR(36) NOT NULL, 
	writer_id VARCHAR(36) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	genre VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(writer_id) REFERENCES users (id)
)

;


CREATE TABLE audit_events (
	id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	action VARCHAR(40) NOT NULL, 
	resource_id VARCHAR(36) NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;


CREATE TABLE chapters (
	id VARCHAR(36) NOT NULL, 
	story_id VARCHAR(36) NOT NULL, 
	position INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	content TEXT NOT NULL, 
	revision INTEGER NOT NULL, 
	intent JSON NOT NULL, 
	state VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (story_id, position), 
	FOREIGN KEY(story_id) REFERENCES stories (id)
)

;


CREATE TABLE invitations (
	id VARCHAR(36) NOT NULL, 
	story_id VARCHAR(36) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (story_id, email), 
	FOREIGN KEY(story_id) REFERENCES stories (id)
)

;


CREATE TABLE snapshots (
	id VARCHAR(36) NOT NULL, 
	chapter_id VARCHAR(36) NOT NULL, 
	revision INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	content TEXT NOT NULL, 
	universe JSON NOT NULL, 
	intent JSON NOT NULL, 
	mode VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chapter_id) REFERENCES chapters (id)
)

;


CREATE TABLE releases (
	id VARCHAR(36) NOT NULL, 
	chapter_id VARCHAR(36) NOT NULL, 
	snapshot_id VARCHAR(36) NOT NULL, 
	reader_id VARCHAR(36) NOT NULL, 
	active INTEGER NOT NULL, 
	progress INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (chapter_id, reader_id), 
	FOREIGN KEY(chapter_id) REFERENCES chapters (id), 
	FOREIGN KEY(snapshot_id) REFERENCES snapshots (id), 
	FOREIGN KEY(reader_id) REFERENCES users (id)
)

;


CREATE TABLE questions (
	id VARCHAR(36) NOT NULL, 
	release_id VARCHAR(36) NOT NULL, 
	text TEXT NOT NULL, 
	category VARCHAR(30) NOT NULL, 
	source VARCHAR(30) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(release_id) REFERENCES releases (id)
)

;


CREATE TABLE feedback (
	id VARCHAR(36) NOT NULL, 
	release_id VARCHAR(36) NOT NULL, 
	reader_id VARCHAR(36) NOT NULL, 
	start INTEGER NOT NULL, 
	"end" INTEGER NOT NULL, 
	quote TEXT NOT NULL, 
	category VARCHAR(30) NOT NULL, 
	text TEXT NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(release_id) REFERENCES releases (id), 
	FOREIGN KEY(reader_id) REFERENCES users (id)
)

;


CREATE TABLE answers (
	id VARCHAR(36) NOT NULL, 
	question_id VARCHAR(36) NOT NULL, 
	release_id VARCHAR(36) NOT NULL, 
	reader_id VARCHAR(36) NOT NULL, 
	text TEXT NOT NULL, 
	confidence INTEGER NOT NULL, 
	emotion VARCHAR(40) NOT NULL, 
	tension INTEGER NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (question_id, reader_id), 
	FOREIGN KEY(question_id) REFERENCES questions (id), 
	FOREIGN KEY(release_id) REFERENCES releases (id), 
	FOREIGN KEY(reader_id) REFERENCES users (id)
)

;