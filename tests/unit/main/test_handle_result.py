from unittest.mock import AsyncMock, Mock, patch
import pytest
from typing import cast

from danbooru_favourites_downloader.main import DownloadMode, handle_result, Context
from danbooru_favourites_downloader.database import PostMetaData
from tests.utils import as_mock



@pytest.fixture
def sample_post():
    return {
        "id": 123,
        "md5": "SADbjf5349bg78D",
        "tag_string_general": "tag1 tag2",
        "tag_string_character": "",
        "tag_string_copyright": "",
        "tag_string_artist": "",
        "tag_string_meta": "",
        "rating": "g",
        "parent_id": None,
        "has_children": False,
        "has_active_children": False,
        "file_ext": "jpg",
    }

@pytest.fixture
def sample_post_meta_data():
    pmd = PostMetaData(123)
    pmd.md5 = "SADbjf5349bg78D"
    pmd.tag_string_general = "tag1 tag2"
    pmd.tag_string_character = ""
    pmd.tag_string_copyright = ""
    pmd.tag_string_artist = ""
    pmd.tag_string_meta = ""
    pmd.rating = "g"
    pmd.parent_id = 0
    pmd.has_children = False
    pmd.has_active_children = False
    pmd.file_ext = "jpg"
    return pmd



@pytest.mark.asyncio()
async def test_handle_result_success_normal(context: Context, sample_post, sample_post_meta_data):
    sample_ret = (True, sample_post)
    
    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(context, sample_ret)                                         

    assert success == 1
    assert errors == 0
    as_mock(context.database.insert_post_data).assert_called_once_with(sample_post_meta_data)
    as_mock(context.database.remove_from_error).assert_not_called()
    as_mock(context.database.insert_id_to_error).assert_not_called()

@pytest.mark.asyncio()
async def test_handle_result_failure_normal(context: Context, sample_post):
    sample_ret = (False, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(context, sample_ret)   

    assert success == 0
    assert errors == 1
    as_mock(context.database.insert_post_data).assert_not_called()
    as_mock(context.database.remove_from_error).assert_not_called()
    as_mock(context.database.insert_id_to_error).assert_called_once_with(sample_post.get('id','ASSERT_FAILURE'))


@pytest.mark.asyncio()
async def test_handle_result_success_retry(context: Context, sample_post, sample_post_meta_data):
    context.mode = DownloadMode.RETRY
    sample_ret = (True, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(context, sample_ret)                                         

    assert success == 1
    assert errors == 0
    
    as_mock(context.database.insert_post_data).assert_called_once_with(sample_post_meta_data)
    as_mock(context.database.remove_from_error).assert_called_once_with(123)
    as_mock(context.database.insert_id_to_error).assert_not_called()

@pytest.mark.asyncio()
async def test_handle_result_failure_retry(context: Context, sample_post):
    context.mode = DownloadMode.RETRY
    sample_ret = (False, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(context, sample_ret)   

    assert success == 0
    assert errors == 0
    as_mock(context.database.insert_post_data).assert_not_called()
    as_mock(context.database.remove_from_error).assert_not_called()
    as_mock(context.database.insert_id_to_error).assert_not_called()
    mock_build.assert_not_called()


@pytest.mark.asyncio()
async def test_handle_result_success_force(context: Context, sample_post, sample_post_meta_data):
    context.mode = DownloadMode.FORCE
    sample_ret = (True, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(context, sample_ret)                                         

    assert success == 1
    assert errors == 0
    as_mock(context.database.insert_post_data).assert_called_once_with(sample_post_meta_data)
    as_mock(context.database.remove_from_error).assert_not_called()
    as_mock(context.database.insert_id_to_error).assert_not_called()

@pytest.mark.asyncio()
async def test_handle_result_failure_force(context: Context, sample_post):
    context.mode = DownloadMode.FORCE
    sample_ret = (False, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(context, sample_ret)   

    assert success == 0
    assert errors == 1
    as_mock(context.database.insert_post_data).assert_not_called()
    as_mock(context.database.remove_from_error).assert_not_called()
    as_mock(context.database.insert_id_to_error).assert_called_once_with(sample_post.get('id','ASSERT_FAILURE'))
