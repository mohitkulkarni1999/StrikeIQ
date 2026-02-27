-- AI Event Log Table Schema
-- Logs all AI system events for debugging and monitoring

CREATE TABLE IF NOT EXISTS ai_event_log (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_event_type ON ai_event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_ai_event_created_at ON ai_event_log(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_event_type_time ON ai_event_log(event_type, created_at);
