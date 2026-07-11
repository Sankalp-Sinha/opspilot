from collections.abc import (
    Iterator,
)

from contextlib import (
    contextmanager,
)

from langgraph.checkpoint.postgres import (
    PostgresSaver,
)

from app.core.config import (
    settings,
)


@contextmanager
def open_postgres_checkpointer(
) -> Iterator[PostgresSaver]:
    with PostgresSaver.from_conn_string(
        settings.langgraph_checkpoint_db_uri
    ) as checkpointer:
        yield checkpointer


def setup_langgraph_checkpointer() -> None:
    with PostgresSaver.from_conn_string(
        settings.langgraph_checkpoint_db_uri
    ) as checkpointer:
        checkpointer.setup()