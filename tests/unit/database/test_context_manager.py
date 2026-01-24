import pytest
from danbooru_favourites_downloader.database import Database, PostMetaData

def test_context_manager():
    with Database(":memory:") as db:
        db.set_newest_downloaded_id(5)
        db.commit()

    with pytest.raises(Exception):
        db.set_newest_downloaded_id(10)