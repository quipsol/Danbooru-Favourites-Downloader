from typing import Any
import pytest
from unittest.mock import AsyncMock, Mock, patch

from danbooru_favourites_downloader.main import select_posts, DownloadMode, Context
from danbooru_favourites_downloader.database import Database
from tests.utils import as_mock

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
            #lambda session, db: ((),{"session": session, "latest_id": 123, "un": "username"}),
            lambda v: ((v, 123),{}),
            True,
        ),
        (
            DownloadMode.RETRY,
            "get_all_error_posts",
            lambda v: ((v,),{}),
            False,
        ),
        (
            DownloadMode.FORCE,
            "get_all_new_posts",
            lambda v: ((v,),{}),
            False,
        ),
    ],
)
async def test_select_posts(context: Context, fake_data,
                            mode, expected_fn, expected_kw_args, expects_db_call):
    context.mode = mode

    as_mock(context.database.get_newest_downloaded_id).return_value = 123

    with (patch("danbooru_favourites_downloader.main.get_all_new_posts", return_value=fake_data) as mock_new,
          patch("danbooru_favourites_downloader.main.get_all_error_posts", return_value=fake_data) as mock_error):
        result = await select_posts(context)

    assert result == fake_data
    assert as_mock(context.database.get_newest_downloaded_id).call_count == (1 if expects_db_call else 0)
    mock = mock_new if expected_fn == "get_all_new_posts" else mock_error
    args, kwargs = expected_kw_args(context)
    mock.assert_called_once_with(*args, **kwargs)






    