"""Add AI signal logs table

Revision ID: add_ai_signal_logs_table_v2
Revises: 2a25798e298c
Create Date: 2026-03-02 09:41:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_ai_signal_logs_table_v2'
down_revision: Union[str, Sequence[str], None] = '2a25798e298c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ai_signal_logs table
    op.execute("""
        CREATE TABLE ai_signal_logs (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            signal VARCHAR(20) NOT NULL,
            confidence FLOAT NOT NULL,
            spot_price FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add indexes for performance
    op.execute("""
        CREATE INDEX idx_ai_signal_logs_symbol_created 
        ON ai_signal_logs(symbol, created_at DESC)
    """)
    
    # Ensure market_snapshot table exists with proper schema
    op.execute("""
        CREATE TABLE IF NOT EXISTS market_snapshot (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            spot_price FLOAT NOT NULL,
            pcr FLOAT NOT NULL,
            total_call_oi FLOAT NOT NULL,
            total_put_oi FLOAT NOT NULL,
            atm_strike FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add index for market_snapshot
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_market_snapshot_symbol_timestamp 
        ON market_snapshot(symbol, timestamp DESC)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS ai_signal_logs")
    # Keep market_snapshot table as it might be used elsewhere
