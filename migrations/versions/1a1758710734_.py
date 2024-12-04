"""empty message

Revision ID: 1a1758710734
Revises: 
Create Date: 2024-12-03 13:00:19.370580

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1a1758710734'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'food_items', ['item_id'], ['id'])
        batch_op.create_foreign_key(None, 'orders', ['order_id'], ['order_id'])
        batch_op.create_foreign_key(None, 'cuisines', ['cuisine_id'], ['id'])
        batch_op.drop_column('price')
        batch_op.drop_column('total_price')
        batch_op.drop_column('quantity')
        batch_op.drop_column('item_name')
        batch_op.drop_column('cuisine')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cuisine', mysql.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('item_name', mysql.VARCHAR(length=100), nullable=False))
        batch_op.add_column(sa.Column('quantity', mysql.INTEGER(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('total_price', mysql.DECIMAL(precision=10, scale=2), nullable=False))
        batch_op.add_column(sa.Column('price', mysql.DECIMAL(precision=10, scale=2), nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    # ### end Alembic commands ###
