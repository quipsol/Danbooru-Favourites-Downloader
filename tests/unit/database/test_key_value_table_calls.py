import pytest
from danbooru_favourites_downloader.database import Database, PostMetaData


@pytest.fixture
def db():
    database = Database(":memory:")
    yield database
    database.close()


def test_set_and_get_newest_downloaded_id(db:Database):
    assert db.get_newest_downloaded_id() == 0

    db.set_newest_downloaded_id(42)
    assert db.get_newest_downloaded_id() == 42

    db.set_newest_downloaded_id(100)
    assert db.get_newest_downloaded_id() == 100