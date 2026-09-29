CREATE EXTENSION IF NOT EXISTS vector;

-- Optional semantic memory index for a later retrieval increment. The current
-- vertical slice retrieves exact reader-owned answer rows instead of embeddings.
-- Every query must join released chapter access, reader_id and chapter_position;
-- a vector similarity result alone is never an authorization decision.
CREATE TABLE IF NOT EXISTS reader_memory_vectors (
    answer_id uuid PRIMARY KEY,
    reader_id uuid NOT NULL,
    story_id uuid NOT NULL,
    chapter_position integer NOT NULL CHECK (chapter_position > 0),
    embedding vector(1536) NOT NULL
);
CREATE INDEX IF NOT EXISTS memory_reader_boundary
    ON reader_memory_vectors (reader_id, story_id, chapter_position);
CREATE INDEX IF NOT EXISTS memory_embedding_hnsw
    ON reader_memory_vectors USING hnsw (embedding vector_cosine_ops);
