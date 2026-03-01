-- StrikeIQ Database Restore Script
-- Loads schema first, then seed data
-- Usage: psql -d strikeiq -f restore_all.sql

-- Start transaction
BEGIN;

-- Echo progress
\echo '=== Loading StrikeIQ Database Schema ==='

-- Load all schema files
\i 'schema/formula_master.sql'
\i 'schema/formula_experience.sql'
\i 'schema/prediction_log.sql'
\i 'schema/outcome_log.sql'
\i 'schema/paper_trade_log.sql'
\i 'schema/market_snapshot.sql'
\i 'schema/ai_event_log.sql'

\echo '=== Schema loaded successfully ==='
\echo '=== Loading Seed Data ==='

-- Load seed data
\i 'seed/formula_master_seed.sql'
\i 'seed/formula_experience_seed.sql'

\echo '=== Seed data loaded successfully ==='

-- Verify data loaded
\echo '=== Verifying Database Setup ==='

SELECT 'formula_master' as table_name, COUNT(*) as record_count FROM formula_master
UNION ALL
SELECT 'formula_experience' as table_name, COUNT(*) as record_count FROM formula_experience
UNION ALL
SELECT 'prediction_log' as table_name, COUNT(*) as record_count FROM prediction_log
UNION ALL
SELECT 'outcome_log' as table_name, COUNT(*) as record_count FROM outcome_log
UNION ALL
SELECT 'paper_trade_log' as table_name, COUNT(*) as record_count FROM paper_trade_log
UNION ALL
SELECT 'market_snapshot' as table_name, COUNT(*) as record_count FROM market_snapshot
UNION ALL
SELECT 'ai_event_log' as table_name, COUNT(*) as record_count FROM ai_event_log;

\echo '=== Database Restore Complete ==='

-- Commit transaction
COMMIT;

-- Show final status
\echo '=== StrikeIQ Database Ready ==='
SELECT 'StrikeIQ AI Database restored successfully!' as status;
