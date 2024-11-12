"""empty message

Revision ID: 445dd80a2360
Revises: 8ee3cfbc3a6c
Create Date: 2024-11-06 15:27:20.503644

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '445dd80a2360'
down_revision = '8ee3cfbc3a6c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sales',
    sa.Column('sale_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('kitchen_id', sa.Integer(), nullable=True),
    sa.Column('cuisine', sa.String(length=50), nullable=True),
    sa.Column('item_name', sa.String(length=100), nullable=False),
    sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('total_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('datetime', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['kitchen_id'], ['kitchens.id'], ),
    sa.PrimaryKeyConstraint('sale_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sales')
    # ### end Alembic commands ###
