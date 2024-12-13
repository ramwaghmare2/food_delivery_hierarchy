"""Initial Migration

Revision ID: 8a212945022b
Revises: 
Create Date: 2024-12-12 12:13:08.565297

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a212945022b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_index('ix_orders_kitchen_id')
        batch_op.drop_index('ix_orders_user_id')
        batch_op.create_foreign_key(None, 'customers', ['user_id'], ['id'])
        batch_op.create_foreign_key(None, 'kitchens', ['kitchen_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_index('ix_orders_user_id', ['user_id'], unique=False)
        batch_op.create_index('ix_orders_kitchen_id', ['kitchen_id'], unique=False)

    # ### end Alembic commands ###