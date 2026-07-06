"""update ck_max_file_per_sesi dari 32 menjadi 35

Revision ID: d7fb418f62fd
Revises: 0fc037f678bf
Create Date: 2026-07-03 13:58:54.754372

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7fb418f62fd'
down_revision = '0fc037f678bf'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE sesi_analisis
        DROP CONSTRAINT ck_max_file_per_sesi
    """)
    op.execute("""
        ALTER TABLE sesi_analisis
        ADD CONSTRAINT ck_max_file_per_sesi
        CHECK (total_file_terunggah <= 35)
    """)


def downgrade():
    op.execute("""
        ALTER TABLE sesi_analisis
        DROP CONSTRAINT ck_max_file_per_sesi
    """)
    op.execute("""
        ALTER TABLE sesi_analisis
        ADD CONSTRAINT ck_max_file_per_sesi
        CHECK (total_file_terunggah <= 32)
    """)
