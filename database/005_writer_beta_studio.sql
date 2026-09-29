-- Additive Writer and Beta Reader tools. Existing releases remain frozen.


CREATE TABLE IF NOT EXISTS story_details (
	story_id VARCHAR(36) NOT NULL, 
	data JSON NOT NULL, 
	PRIMARY KEY (story_id), 
	FOREIGN KEY(story_id) REFERENCES stories (id)
)

;


CREATE TABLE IF NOT EXISTS beta_profiles (
	user_id VARCHAR(36) NOT NULL, 
	data JSON NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE IF NOT EXISTS reading_positions (
	release_id VARCHAR(36) NOT NULL, 
	"offset" INTEGER NOT NULL, 
	PRIMARY KEY (release_id), 
	FOREIGN KEY(release_id) REFERENCES releases (id)
)

;


CREATE TABLE IF NOT EXISTS reader_observations (
	id VARCHAR(36) NOT NULL, 
	release_id VARCHAR(36) NOT NULL, 
	snapshot_id VARCHAR(36) NOT NULL, 
	reader_id VARCHAR(36) NOT NULL, 
	kind VARCHAR(30) NOT NULL, 
	target VARCHAR(200) NOT NULL, 
	value INTEGER NOT NULL, 
	confidence INTEGER NOT NULL, 
	explanation TEXT NOT NULL, 
	evidence TEXT NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(release_id) REFERENCES releases (id), 
	FOREIGN KEY(snapshot_id) REFERENCES snapshots (id), 
	FOREIGN KEY(reader_id) REFERENCES users (id)
)

;


CREATE TABLE IF NOT EXISTS overall_feedback (
	id VARCHAR(36) NOT NULL, 
	story_id VARCHAR(36) NOT NULL, 
	reader_id VARCHAR(36) NOT NULL, 
	release_id VARCHAR(36), 
	scope VARCHAR(20) NOT NULL, 
	text TEXT NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(story_id) REFERENCES stories (id), 
	FOREIGN KEY(reader_id) REFERENCES users (id), 
	FOREIGN KEY(release_id) REFERENCES releases (id)
)

;


CREATE TABLE IF NOT EXISTS helpful_ratings (
	key VARCHAR(100) NOT NULL, 
	writer_id VARCHAR(36) NOT NULL, 
	reader_id VARCHAR(36) NOT NULL, 
	rating INTEGER NOT NULL, 
	PRIMARY KEY (key), 
	FOREIGN KEY(writer_id) REFERENCES users (id), 
	FOREIGN KEY(reader_id) REFERENCES users (id)
)

;


CREATE TABLE IF NOT EXISTS question_placements (
	question_id VARCHAR(36) NOT NULL, 
	data JSON NOT NULL, 
	PRIMARY KEY (question_id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
)

;


CREATE TABLE IF NOT EXISTS writing_entries (
	id VARCHAR(36) NOT NULL, 
	story_id VARCHAR(36) NOT NULL, 
	chapter_id VARCHAR(36) NOT NULL, 
	word_count INTEGER NOT NULL, 
	delta INTEGER NOT NULL, 
	created FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(story_id) REFERENCES stories (id), 
	FOREIGN KEY(chapter_id) REFERENCES chapters (id)
)

;