"""empty message

Revision ID: 224c934278f5
Revises: 2bd8071cdc2e
Create Date: 2020-02-26 21:42:35.087093

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '224c934278f5'
down_revision = '2bd8071cdc2e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('descriptions', sa.Column('created', sa.DateTime(), nullable=False))
    op.add_column('photos', sa.Column('created', sa.DateTime(), nullable=False))
    op.add_column('products', sa.Column('created', sa.DateTime(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'created')
    op.drop_column('photos', 'created')
    op.drop_column('descriptions', 'created')
    # ### end Alembic commands ###