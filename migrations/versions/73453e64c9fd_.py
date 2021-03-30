"""empty message

Revision ID: 73453e64c9fd
Revises: 
Create Date: 2021-03-30 03:50:33.806280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73453e64c9fd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('character',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('birth_day', sa.DateTime(), nullable=False),
    sa.Column('gender', sa.String(length=100), nullable=False),
    sa.Column('height', sa.Integer(), nullable=False),
    sa.Column('skin_color', sa.String(length=100), nullable=False),
    sa.Column('hair_color', sa.String(length=100), nullable=False),
    sa.Column('eye_color', sa.String(length=100), nullable=False),
    sa.Column('favorite_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['favorite_id'], ['favorite.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('planet',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('climate', sa.String(length=100), nullable=False),
    sa.Column('population', sa.Integer(), nullable=False),
    sa.Column('terrain', sa.String(length=100), nullable=False),
    sa.Column('rotation_period', sa.Integer(), nullable=False),
    sa.Column('orbital_period', sa.Integer(), nullable=False),
    sa.Column('diameter', sa.Integer(), nullable=False),
    sa.Column('favorite_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['favorite_id'], ['favorite.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('planet')
    op.drop_table('character')
    # ### end Alembic commands ###
