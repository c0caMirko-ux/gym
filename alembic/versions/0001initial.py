
# alembic/versions/0001_initial.py
"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # For brevity: use raw SQL to create schema and key objects (adapt if needed)
    op.execute("CREATE SCHEMA IF NOT EXISTS gym;")
    # NOTE: You can paste the DDL from el script inicial aquí (ENUMs, tables, triggers).
    # Para mantener el migration legible, recomiendo ejecutar el DDL completo que te compartí
    # desde un archivo SQL o usar el autogenerate de Alembic.
    pass

def downgrade():
    op.execute("DROP SCHEMA IF EXISTS gym CASCADE;")
