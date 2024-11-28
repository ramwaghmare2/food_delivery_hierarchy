"""Intital Miagration

Revision ID: 44f57b8c1d82
Revises: 
Create Date: 2024-11-26 13:01:42.242373

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44f57b8c1d82'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('distributors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('online_status', sa.Boolean(), nullable=True))

    with op.batch_alter_table('kitchens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('online_status', sa.Boolean(), nullable=True))

    with op.batch_alter_table('managers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('online_status', sa.Boolean(), nullable=True))

    with op.batch_alter_table('super_distributors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('online_status', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('super_distributors', schema=None) as batch_op:
        batch_op.drop_column('online_status')

    with op.batch_alter_table('managers', schema=None) as batch_op:
        batch_op.drop_column('online_status')

    with op.batch_alter_table('kitchens', schema=None) as batch_op:
        batch_op.drop_column('online_status')

    with op.batch_alter_table('distributors', schema=None) as batch_op:
        batch_op.drop_column('online_status')

    # ### end Alembic commands ###
