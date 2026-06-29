from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, sessionmaker

from src.constants import CONN_STR

# pool_pre_ping validates a pooled connection before use and transparently
# reconnects if the server dropped it (e.g. a managed Postgres restarting or
# closing idle connections), which matters for the long rebuild and the
# always-on updater. pool_recycle proactively refreshes connections that have
# been idle too long.
engine = create_engine(
    CONN_STR,
    pool_pre_ping=True,
    pool_recycle=1800,
    # Reads now run in a thread pool (see alru_cache), so allow more concurrent
    # connections than the default 5 + 10 to avoid checkout contention.
    pool_size=10,
    max_overflow=20,
)

Session = sessionmaker(bind=engine)


# Only for type hints, doesn't enable slots
# Mirror to avoid intermediate commits to DB
class Base(MappedAsDataclass, DeclarativeBase):
    pass


def clean_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
