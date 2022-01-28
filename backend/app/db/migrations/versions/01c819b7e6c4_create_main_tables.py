"""create_main_tables
Revision ID: 01c819b7e6c4
Revises: 
Create Date: 2022-01-26 09:36:00.802514
"""

import sqlalchemy as sa


from alembic import op



revision = '01c819b7e6c4'
down_revision = None
branch_labels = None
depends_on = None


def create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("password", sa.Text, nullable=False)
    )

def upgrade() -> None:
    create_users_table()

def downgrade() -> None:
    op.drop_table("users")
