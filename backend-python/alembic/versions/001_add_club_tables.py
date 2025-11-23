"""Add club tables

Revision ID: 001_add_club_tables
Revises:
Create Date: 2025-11-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_club_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create clubs table
    op.create_table(
        'clubs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('encrypted_name', sa.LargeBinary(length=1024), nullable=False),
        sa.Column('encrypted_description', sa.LargeBinary(length=5120), nullable=True),
        sa.Column('encrypted_profile_picture', sa.LargeBinary(), nullable=True),
        sa.Column('encryption_iv', sa.LargeBinary(length=16), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('members_can_post', sa.Boolean(), nullable=False),
        sa.Column('members_can_invite', sa.Boolean(), nullable=False),
        sa.Column('max_members', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clubs_owner_user_id'), 'clubs', ['owner_user_id'], unique=False)

    # Create club_members table
    op.create_table(
        'club_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('club_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('joined', sa.DateTime(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('encrypted_aes_key', sa.LargeBinary(length=512), nullable=False),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('club_id', 'user_id', name='uq_club_user')
    )
    op.create_index(op.f('ix_club_members_club_id'), 'club_members', ['club_id'], unique=False)
    op.create_index(op.f('ix_club_members_user_id'), 'club_members', ['user_id'], unique=False)

    # Create club_events table
    op.create_table(
        'club_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('club_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('expiry', sa.DateTime(), nullable=False),
        sa.Column('encrypted_event', sa.LargeBinary(length=5120), nullable=False),
        sa.Column('encryption_iv', sa.LargeBinary(length=16), nullable=False),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('club_id', 'id')
    )
    op.create_index(op.f('ix_club_events_club_id'), 'club_events', ['club_id'], unique=False)
    op.create_index(op.f('ix_club_events_expiry'), 'club_events', ['expiry'], unique=False)
    op.create_index(op.f('ix_club_events_user_id'), 'club_events', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_club_events_user_id'), table_name='club_events')
    op.drop_index(op.f('ix_club_events_expiry'), table_name='club_events')
    op.drop_index(op.f('ix_club_events_club_id'), table_name='club_events')
    op.drop_table('club_events')

    op.drop_index(op.f('ix_club_members_user_id'), table_name='club_members')
    op.drop_index(op.f('ix_club_members_club_id'), table_name='club_members')
    op.drop_table('club_members')

    op.drop_index(op.f('ix_clubs_owner_user_id'), table_name='clubs')
    op.drop_table('clubs')
