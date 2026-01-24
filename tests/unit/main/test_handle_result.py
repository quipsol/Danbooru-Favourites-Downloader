from unittest.mock import AsyncMock, Mock, patch
import pytest

from danbooru_favourites_downloader.main import DownloadMode, handle_result
from danbooru_favourites_downloader.database import PostMetaData


@pytest.fixture
def fake_db():
    return Mock()

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
async def test_handle_result_success_normal(fake_db, sample_post, sample_post_meta_data):
    mode = DownloadMode.NORMAL
    sample_ret = (True, sample_post)
    
    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(sample_ret, fake_db, mode)                                         

    assert success == 1
    assert errors == 0
    fake_db.insert_post_data.assert_called_once_with(sample_post_meta_data)
    fake_db.remove_from_error.assert_not_called()
    fake_db.insert_id_to_error.assert_not_called()

@pytest.mark.asyncio()
async def test_handle_result_failure_normal(fake_db, sample_post):
    mode = DownloadMode.NORMAL
    sample_ret = (False, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(sample_ret, fake_db, mode)   

    assert success == 0
    assert errors == 1
    fake_db.insert_post_data.assert_not_called()
    fake_db.remove_from_error.assert_not_called()
    fake_db.insert_id_to_error.assert_called_once_with(sample_post.get('id','ASSERT_FAILURE'))


@pytest.mark.asyncio()
async def test_handle_result_success_retry(fake_db, sample_post, sample_post_meta_data):
    mode = DownloadMode.RETRY
    sample_ret = (True, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(sample_ret, fake_db, mode)                                         

    assert success == 1
    assert errors == 0
    fake_db.insert_post_data.assert_called_once_with(sample_post_meta_data)
    fake_db.remove_from_error.assert_called_once_with(123)
    fake_db.insert_id_to_error.assert_not_called()

@pytest.mark.asyncio()
async def test_handle_result_failure_retry(fake_db, sample_post):
    mode = DownloadMode.RETRY
    sample_ret = (False, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(sample_ret, fake_db, mode)   

    assert success == 0
    assert errors == 0
    fake_db.insert_post_data.assert_not_called()
    fake_db.remove_from_error.assert_not_called()
    fake_db.insert_id_to_error.assert_not_called()
    mock_build.assert_not_called()


@pytest.mark.asyncio()
async def test_handle_result_success_force(fake_db, sample_post, sample_post_meta_data):
    mode = DownloadMode.FORCE
    sample_ret = (True, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(sample_ret, fake_db, mode)                                         

    assert success == 1
    assert errors == 0
    fake_db.insert_post_data.assert_called_once_with(sample_post_meta_data)
    fake_db.remove_from_error.assert_not_called()
    fake_db.insert_id_to_error.assert_not_called()

@pytest.mark.asyncio()
async def test_handle_result_failure_force(fake_db, sample_post):
    mode = DownloadMode.FORCE
    sample_ret = (False, sample_post)

    with patch("danbooru_favourites_downloader.main.build_metadata", return_value=sample_post_meta_data) as mock_build:
        success, errors = await handle_result(sample_ret, fake_db, mode)   

    assert success == 0
    assert errors == 1
    fake_db.insert_post_data.assert_not_called()
    fake_db.remove_from_error.assert_not_called()
    fake_db.insert_id_to_error.assert_called_once_with(sample_post.get('id','ASSERT_FAILURE'))
