"""Create ai_signal_logs table

Revision ID: create_ai_signal_logs
Revises: 2a25798e298c
Create Date: 2026-03-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_ai_signal_logs'
down_revision = '2a25798e298c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_signal_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('symbol', sa.String(50)),
        sa.Column('signal', sa.String(50)),
        sa.Column('confidence', sa.Float),
        sa.Column('spot_price', sa.Float),
        sa.Column('timestamp', sa.DateTime)
    )


def downgrade():
    op.drop_table('ai_signal_logs')
