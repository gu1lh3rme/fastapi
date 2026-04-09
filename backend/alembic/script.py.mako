"""${message}

Revisão: ${up_revision}
Revisão anterior: ${down_revision | comma,n}
Branch labels: ${branch_labels}
Depends on: ${depends_on}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# Identificadores da revisão
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Aplica as mudanças no banco de dados."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Reverte as mudanças no banco de dados."""
    ${downgrades if downgrades else "pass"}
