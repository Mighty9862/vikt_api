"""WebSocket full

Revision ID: 1f564fe1e9bc
Revises: 0d24b40856c6
Create Date: 2025-02-13 02:16:19.649466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f564fe1e9bc'
down_revision: Union[str, None] = '0d24b40856c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('gamestatus', 'current_question_image',
               existing_type=sa.VARCHAR(length=1000),
               nullable=True)
    op.alter_column('gamestatus', 'current_answer_image',
               existing_type=sa.VARCHAR(length=1000),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('gamestatus', 'current_answer_image',
               existing_type=sa.VARCHAR(length=1000),
               nullable=False)
    op.alter_column('gamestatus', 'current_question_image',
               existing_type=sa.VARCHAR(length=1000),
               nullable=False)
    # ### end Alembic commands ###
