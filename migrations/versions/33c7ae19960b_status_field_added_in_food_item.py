"""status field added in food Item

Revision ID: 33c7ae19960b
Revises: 
Create Date: 2024-11-28 12:11:55.261530

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '33c7ae19960b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Boolean(), nullable=True))
        batch_op.drop_column('online_status')

    with op.batch_alter_table('food_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('activated', 'deactivated'), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('food_items', schema=None) as batch_op:
        batch_op.drop_column('status')

    with op.batch_alter_table('admins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('online_status', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
        batch_op.drop_column('status')

    # ### end Alembic commands ###
