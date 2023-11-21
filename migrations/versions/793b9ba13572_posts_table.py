"""posts table

Revision ID: 793b9ba13572
Revises: 71d56004ced0
Create Date: 2023-11-20 23:58:22.712494

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '793b9ba13572'
down_revision = '71d56004ced0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('post_info',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(length=140), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user_info.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('post_info', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_post_info_timestamp'), ['timestamp'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post_info', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_post_info_timestamp'))

    op.drop_table('post_info')
    # ### end Alembic commands ###
