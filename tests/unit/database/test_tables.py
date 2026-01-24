import pytest
from danbooru_favourites_downloader.database import Database, PostMetaData


@pytest.fixture
def db():
    database = Database(":memory:")
    yield database
    database.close()



def test_delete_tables(db:Database):
    db.insert_id_to_error(1)
    db.set_newest_downloaded_id(10)
    db.commit()

    db.delete_tables()

    assert db.get_error_ids() == []
    assert db.get_newest_downloaded_id() == 0


def test_create_tables(db:Database):
    # on Database context-manager __init__ create_tables() is called
    tables = db.cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    assert ("key_value_pairs",) in tables