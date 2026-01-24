import pytest
from danbooru_favourites_downloader.database import Database, PostMetaData


@pytest.fixture
def db():
    database = Database(":memory:")
    yield database
    database.close()


def test_get_error_ids(db:Database):
    assert db.get_error_ids() == []


def test_insert_error_ids(db:Database):
    db.insert_id_to_error(5)
    db.insert_id_to_error(10)
    db.commit()

    assert sorted(db.get_error_ids()) == [5, 10]

def test_remove_from_error(db:Database):
    db.insert_id_to_error(3)
    db.commit()
    db.remove_from_error(3)
    db.commit()
    
    assert db.get_error_ids() == []