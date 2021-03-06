"""Add tables aaaa

Revision ID: d87761df646f
Revises: 8cfe5befdaec
Create Date: 2016-07-21 00:21:30.939974

"""

# revision identifiers, used by Alembic.
revision = 'd87761df646f'
down_revision = '8cfe5befdaec'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('server',
    sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('member',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('joined_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('server_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['server_id'], ['server.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message',
    sa.Column('id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('content', sa.String(), nullable=True),
    sa.Column('deleted', sa.Boolean(), nullable=True),
    sa.Column('channel_id', sa.Integer(), nullable=True),
    sa.Column('member_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['channel_id'], ['channel.id'], ),
    sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('nickname_change',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('before', sa.String(), nullable=True),
    sa.Column('after', sa.String(), nullable=True),
    sa.Column('member_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('username_change',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('before', sa.String(), nullable=True),
    sa.Column('after', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('channel', sa.Column('server_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'channel', 'server', ['server_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'channel', type_='foreignkey')
    op.drop_column('channel', 'server_id')
    op.drop_table('username_change')
    op.drop_table('user')
    op.drop_table('server')
    op.drop_table('nickname_change')
    op.drop_table('message')
    op.drop_table('member')
    ### end Alembic commands ###
