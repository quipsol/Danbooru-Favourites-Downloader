import pytest
from danbooru_favourites_downloader.database import Database, PostMetaData


@pytest.fixture
def db():
    database = Database(":memory:")
    yield database
    database.close()

def test_insert_post_data(db):
    post = PostMetaData(1)
    post.md5 = "abc"
    post.rating = "s"
    post.has_children = True
    post.has_active_children = False
    post.file_ext = "jpg"

    db.insert_post_data(post)
    db.commit()

    rows = db.cur.execute("SELECT * FROM posts WHERE post_id = 1").fetchone()
    assert rows is not None
    assert rows[0] == 1
    assert rows[1] == "abc"
    assert rows[7] == "s"