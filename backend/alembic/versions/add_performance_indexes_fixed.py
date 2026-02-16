"""Add performance indexes for option chain queries

Revision ID: add_performance_indexes_fixed
Revises: 2a25798e298c
Create Date: 2026-02-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_performance_indexes_fixed'
down_revision = '2a25798e298c'
branch_labels = None
depends_on = None

def upgrade():
    # Add indexes for market snapshots
    op.create_index('idx_market_snapshots_symbol_timestamp', 
                   ['symbol', 'timestamp'], 
                   unique=False,
                   table_name='market_snapshots')
    
    # Add indexes for option chain snapshots
    op.create_index('idx_option_chain_symbol_expiry', 
                   ['symbol', 'expiry'], 
                   unique=False,
                   table_name='option_chain_snapshots')
    
    op.create_index('idx_option_chain_strike_expiry', 
                   ['strike', 'expiry'], 
                   unique=False,
                   table_name='option_chain_snapshots')
    
    # Add indexes for smart money predictions
    op.create_index('idx_smart_money_symbol_timestamp', 
                   ['symbol', 'timestamp'], 
                   unique=False,
                   table_name='smart_money_predictions')

def downgrade():
    # Remove indexes
    op.drop_index('idx_market_snapshots_symbol_timestamp', table_name='market_snapshots')
    op.drop_index('idx_option_chain_symbol_expiry', table_name='option_chain_snapshots')
    op.drop_index('idx_option_chain_strike_expiry', table_name='option_chain_snapshots')
    op.drop_index('idx_smart_money_symbol_timestamp', table_name='smart_money_predictions')
