"""add media urls to biodiversity

Revision ID: ee587e61206e
Revises: adb7855a2edc
Create Date: 2026-09-14 11:56:10.212285

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'ee587e61206e'
down_revision: Union[str, Sequence[str], None] = 'adb7855a2edc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('biodiversity_observations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photo_urls', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('video_urls', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('biodiversity_observations', schema=None) as batch_op:
        batch_op.drop_column('video_urls')
        batch_op.drop_column('photo_urls')
