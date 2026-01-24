from typing import Any
import pytest
from unittest.mock import AsyncMock, Mock, patch

from danbooru_favourites_downloader.main import select_posts, DownloadMode
from danbooru_favourites_downloader.database import Database

@pytest.fixture
def fake_db():
    return Mock()

@pytest.fixture
def fake_session():
    return Mock()

@pytest.fixture
def fake_data():
    return [{
        "id": 123,
        "md5": "12345f5349bg78D",
        "tag_string_general": "tag1 tag2",
        "rating": "g",
        "file_ext": "jpg",
    },{
        "id": 987,
        "md5": "98765f5349bg78D",
        "tag_string_general": "tag3 tag4",
        "rating": "e",
        "file_ext": "png",
    }]


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    "mode, expected_fn, expected_kw_args, expects_db_call",
    [
        (
            DownloadMode.NORMAL,
            "get_all_new_posts",
            lambda session, db: ((),{"session": session, "latest_id": 123}),
            True,
        ),
        (
            DownloadMode.RETRY,
            "get_all_error_posts",
            lambda session, db: ((session, db),{}),
            False,
        ),
        (
            DownloadMode.FORCE,
            "get_all_new_posts",
            lambda session, db: ((session,),{}),
            False,
        ),
    ],
)
async def test_select_posts(fake_db, fake_session, fake_data,
                            mode, expected_fn, expected_kw_args, expects_db_call):
    
    fake_db.get_newest_downloaded_id.return_value = 123

    with (patch("danbooru_favourites_downloader.main.get_all_new_posts", return_value=fake_data) as mock_new,
          patch("danbooru_favourites_downloader.main.get_all_error_posts", return_value=fake_data) as mock_error):
        result = await select_posts(fake_db, fake_session, mode)

    assert result == fake_data
    assert fake_db.get_newest_downloaded_id.call_count == (1 if expects_db_call else 0)
    mock = mock_new if expected_fn == "get_all_new_posts" else mock_error
    args, kwargs = expected_kw_args(fake_session, fake_db)
    mock.assert_called_once_with(*args, **kwargs)






    