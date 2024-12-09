"""Add manager_id to kitchens

Revision ID: eb771dc9d825
Revises: e8979208f5e3
Create Date: 2024-12-06 16:28:38.748902

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb771dc9d825'
down_revision = 'e8979208f5e3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('kitchens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('manager_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'managers', ['manager_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('kitchens', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('manager_id')

    # ### end Alembic commands ###
