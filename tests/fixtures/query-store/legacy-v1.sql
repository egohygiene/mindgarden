-- The actual previously shipped generated cache layout; synthetic rows are
-- supplied by the test's explicitly authorized index. No real data is stored.
CREATE TABLE metadata (id TEXT PRIMARY KEY, value BLOB NOT NULL);
CREATE TABLE records (id TEXT PRIMARY KEY, value BLOB NOT NULL);
CREATE TABLE edges (source TEXT, target TEXT, type TEXT, value BLOB NOT NULL);
CREATE INDEX outgoing ON edges(source, type);
CREATE INDEX incoming ON edges(target, type);
CREATE VIRTUAL TABLE lexical USING fts5(id UNINDEXED, tokens, tokenize='ascii');
PRAGMA user_version=1;
