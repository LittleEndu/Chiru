"""Add changed_at column to Username/NicknameChange

Revision ID: 570e403b206f
Revises: 0741024a61bb
Create Date: 2016-07-21 00:48:57.146055

"""

# revision identifiers, used by Alembic.
revision = '570e403b206f'
down_revision = '0741024a61bb'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('nickname_change', sa.Column('changed_at', sa.DateTime(), nullable=True))
    op.add_column('username_change', sa.Column('changed_at', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('username_change', 'changed_at')
    op.drop_column('nickname_change', 'changed_at')
    ### end Alembic commands ###