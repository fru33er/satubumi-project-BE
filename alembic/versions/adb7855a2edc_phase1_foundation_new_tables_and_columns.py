"""phase1_foundation_new_tables_and_columns

Revision ID: adb7855a2edc
Revises: 
Create Date: 2026-08-31 18:01:09.255495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adb7855a2edc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — Phase 1 Foundation."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ── Modify existing tables ────────────────────────────────────────────────

    # alerts
    existing_alert_cols = [c['name'] for c in inspector.get_columns('alerts')]
    with op.batch_alter_table('alerts', schema=None) as batch_op:
        if 'created_by' not in existing_alert_cols:
            batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
        if 'source_url' not in existing_alert_cols:
            batch_op.add_column(sa.Column('source_url', sa.String(length=500), nullable=True))

    # articles
    existing_article_cols = [c['name'] for c in inspector.get_columns('articles')]
    with op.batch_alter_table('articles', schema=None) as batch_op:
        if 'title_en' not in existing_article_cols:
            batch_op.add_column(sa.Column('title_en', sa.String(length=255), nullable=True))
        if 'content_en' not in existing_article_cols:
            batch_op.add_column(sa.Column('content_en', sa.Text(), nullable=True))
        if 'image_url' not in existing_article_cols:
            batch_op.add_column(sa.Column('image_url', sa.String(length=500), nullable=True))
        if 'topic' not in existing_article_cols:
            batch_op.add_column(sa.Column('topic', sa.String(length=50), nullable=True))
        if 'is_featured' not in existing_article_cols:
            batch_op.add_column(sa.Column('is_featured', sa.Boolean(), nullable=True))
        if 'view_count' not in existing_article_cols:
            batch_op.add_column(sa.Column('view_count', sa.Integer(), nullable=True))

    # field_reports
    existing_fr_cols = [c['name'] for c in inspector.get_columns('field_reports')]
    with op.batch_alter_table('field_reports', schema=None) as batch_op:
        if 'video_urls' not in existing_fr_cols:
            batch_op.add_column(sa.Column('video_urls', sa.JSON(), nullable=True))
        if 'tree_record_id' not in existing_fr_cols:
            batch_op.add_column(sa.Column('tree_record_id', sa.Integer(), nullable=True))
        if 'biodiversity_id' not in existing_fr_cols:
            batch_op.add_column(sa.Column('biodiversity_id', sa.Integer(), nullable=True))

    # project_activities: rename date -> activity_date if needed
    existing_act_cols = [c['name'] for c in inspector.get_columns('project_activities')]
    if 'date' in existing_act_cols and 'activity_date' not in existing_act_cols:
        with op.batch_alter_table('project_activities', schema=None) as batch_op:
            batch_op.alter_column('date', new_column_name='activity_date')

    # projects
    existing_proj_cols = [c['name'] for c in inspector.get_columns('projects')]
    with op.batch_alter_table('projects', schema=None) as batch_op:
        if 'project_type' not in existing_proj_cols:
            batch_op.add_column(sa.Column('project_type', sa.String(length=100), nullable=True))
        if 'start_date' not in existing_proj_cols:
            batch_op.add_column(sa.Column('start_date', sa.Date(), nullable=True))
        if 'end_date' not in existing_proj_cols:
            batch_op.add_column(sa.Column('end_date', sa.Date(), nullable=True))
        if 'country' not in existing_proj_cols:
            batch_op.add_column(sa.Column('country', sa.String(length=100), nullable=True))
        if 'province' not in existing_proj_cols:
            batch_op.add_column(sa.Column('province', sa.String(length=100), nullable=True))
        if 'district' not in existing_proj_cols:
            batch_op.add_column(sa.Column('district', sa.String(length=100), nullable=True))

    # tree_records
    existing_tr_cols = [c['name'] for c in inspector.get_columns('tree_records')]
    with op.batch_alter_table('tree_records', schema=None) as batch_op:
        if 'created_by' not in existing_tr_cols:
            batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))


    # ── Create new tables ─────────────────────────────────────────────────────
    existing_tables = inspector.get_table_names()

    if 'monitoring_plots' not in existing_tables:
        op.create_table('monitoring_plots',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('plot_code', sa.String(length=100), nullable=False),
            sa.Column('plot_name', sa.String(length=255), nullable=True),
            sa.Column('plot_type', sa.String(length=50), nullable=True),
            sa.Column('location_geojson', sa.JSON(), nullable=True),
            sa.Column('area_ha', sa.Float(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        with op.batch_alter_table('monitoring_plots', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_monitoring_plots_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_monitoring_plots_project_id'), ['project_id'], unique=False)

    if 'tree_measurements' not in existing_tables:
        op.create_table('tree_measurements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tree_record_id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('measurement_date', sa.Date(), nullable=False),
            sa.Column('height_cm', sa.Float(), nullable=True),
            sa.Column('dbh_cm', sa.Float(), nullable=True),
            sa.Column('condition', sa.String(length=50), nullable=True),
            sa.Column('is_alive', sa.Boolean(), nullable=True),
            sa.Column('measured_by', sa.String(length=255), nullable=True),
            sa.Column('photo_urls', sa.JSON(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tree_record_id'], ['tree_records.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        with op.batch_alter_table('tree_measurements', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_tree_measurements_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_tree_measurements_project_id'), ['project_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_tree_measurements_tree_record_id'), ['tree_record_id'], unique=False)

    if 'landscape_snapshots' not in existing_tables:
        op.create_table('landscape_snapshots',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('snapshot_date', sa.Date(), nullable=False),
            sa.Column('data_source', sa.String(length=100), nullable=True),
            sa.Column('forest_cover_ha', sa.Float(), nullable=True),
            sa.Column('deforestation_ha', sa.Float(), nullable=True),
            sa.Column('restoration_ha', sa.Float(), nullable=True),
            sa.Column('land_cleared_ha', sa.Float(), nullable=True),
            sa.Column('fire_ha', sa.Float(), nullable=True),
            sa.Column('ndvi_mean', sa.Float(), nullable=True),
            sa.Column('ndvi_min', sa.Float(), nullable=True),
            sa.Column('ndvi_max', sa.Float(), nullable=True),
            sa.Column('geojson_data', sa.JSON(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        with op.batch_alter_table('landscape_snapshots', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_landscape_snapshots_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_landscape_snapshots_project_id'), ['project_id'], unique=False)

    if 'project_members' not in existing_tables:
        op.create_table('project_members',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=False),
            sa.Column('assigned_at', sa.DateTime(), nullable=True),
            sa.Column('assigned_by', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
        )
        with op.batch_alter_table('project_members', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_project_members_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_project_members_project_id'), ['project_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_project_members_user_id'), ['user_id'], unique=False)



def downgrade() -> None:
    """Downgrade schema — rollback Phase 1."""
    # Drop new tables
    op.drop_index(op.f('ix_project_members_user_id'), table_name='project_members')
    op.drop_index(op.f('ix_project_members_project_id'), table_name='project_members')
    op.drop_index(op.f('ix_project_members_id'), table_name='project_members')
    op.drop_table('project_members')

    op.drop_index(op.f('ix_landscape_snapshots_project_id'), table_name='landscape_snapshots')
    op.drop_index(op.f('ix_landscape_snapshots_id'), table_name='landscape_snapshots')
    op.drop_table('landscape_snapshots')

    op.drop_index(op.f('ix_tree_measurements_tree_record_id'), table_name='tree_measurements')
    op.drop_index(op.f('ix_tree_measurements_project_id'), table_name='tree_measurements')
    op.drop_index(op.f('ix_tree_measurements_id'), table_name='tree_measurements')
    op.drop_table('tree_measurements')

    op.drop_index(op.f('ix_monitoring_plots_project_id'), table_name='monitoring_plots')
    op.drop_index(op.f('ix_monitoring_plots_id'), table_name='monitoring_plots')
    op.drop_table('monitoring_plots')

    # Rollback column changes
    with op.batch_alter_table('tree_records', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tree_records_created_by', type_='foreignkey')
        batch_op.drop_column('created_by')

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('district')
        batch_op.drop_column('province')
        batch_op.drop_column('country')
        batch_op.drop_column('end_date')
        batch_op.drop_column('start_date')
        batch_op.drop_column('project_type')

    with op.batch_alter_table('project_activities', schema=None) as batch_op:
        batch_op.alter_column('activity_date', new_column_name='date')

    with op.batch_alter_table('field_reports', schema=None) as batch_op:
        batch_op.drop_constraint('fk_field_reports_biodiversity', type_='foreignkey')
        batch_op.drop_constraint('fk_field_reports_tree_record', type_='foreignkey')
        batch_op.drop_column('biodiversity_id')
        batch_op.drop_column('tree_record_id')
        batch_op.drop_column('video_urls')

    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_articles_topic'))
        batch_op.drop_index(batch_op.f('ix_articles_is_featured'))
        batch_op.drop_column('view_count')
        batch_op.drop_column('is_featured')
        batch_op.drop_column('topic')
        batch_op.drop_column('image_url')
        batch_op.drop_column('content_en')
        batch_op.drop_column('title_en')

    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_alerts_created_by', type_='foreignkey')
        batch_op.drop_column('source_url')
        batch_op.drop_column('created_by')
