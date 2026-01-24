import pytest
import aiohttp
from aioresponses import aioresponses, CallbackResult
from yarl import URL
import re

from danbooru_favourites_downloader.main import select_posts, DownloadMode
from danbooru_favourites_downloader.database import Database, PostMetaData

@pytest.fixture
def db():
    database = Database(":memory:")
    yield database
    database.close()

@pytest.mark.asyncio
@pytest.mark.parametrize("latest_id",[(22), (0),(9999999)])
async def test_select_posts_normal_mode(db:Database, latest_id:int):
    if latest_id != 0: # 0 should be default return value for db.get_newest_download_id() => dont write it into database
        db.set_newest_downloaded_id(latest_id)
        db.commit()

    pages = [
        [{"id": 105}, {"id": 67}, {"id": 100}, {"id": 99}],
        [{"id": 11}, {"id": 22}, {"id": 33}, {"id": 44}],
        [],
    ]
    call_count = 0
    def callback(url:URL, **kwargs):
        nonlocal call_count
        payload = pages[call_count]
        call_count += 1
        return CallbackResult(status=200, payload=payload)
    url_pattern = re.compile(r"https://danbooru\.donmai\.us/posts\.json.*")
    un = "username"

    with aioresponses() as mocked:
        mocked.get(url_pattern, callback=callback, repeat=True)
        async with aiohttp.ClientSession() as session:
            

            posts = await select_posts(
                database=db,
                session=session,
                mode=DownloadMode.NORMAL,
                un=un
            )


    assert len(mocked.requests) == (2 if latest_id == 22 else 3)
    post_ids = [p["id"] for p in posts]
    assert post_ids == ([105, 67, 100, 99, 11] if latest_id == 22 else [105, 67, 100, 99, 11, 22, 33, 44])


@pytest.mark.asyncio
@pytest.mark.parametrize(
     "error_ids",
     [
          (
            [10, 20, 30, 40]   
          ),
          (
            []
          )
     ]
)
async def test_select_posts_retry_mode(db:Database, error_ids:list[int]):
    for id in error_ids:
         db.insert_id_to_error(id)
    
    url = "https://danbooru.donmai.us/posts/{0}.json"
    un = "username"

    with aioresponses() as mocked:
        for id in error_ids:
            mocked.get(
                url.format(id),
                payload={"id": id, "other": "ignore this"}
            )
        
        async with aiohttp.ClientSession() as session:
            posts = await select_posts(
                database=db,
                session=session,
                mode=DownloadMode.RETRY,
                un=un
            )
    
    post_ids = [p["id"] for p in posts]
    assert post_ids == error_ids


@pytest.mark.asyncio
@pytest.mark.parametrize("latest_id",[(22), (0)])
async def test_select_posts_force_mode(db:Database, latest_id:int):
    '''
    force mode should always grab all IDs and ignore any latest_id that might exist inside the database
    '''
    if latest_id != 0:
        db.set_newest_downloaded_id(latest_id)
        db.commit()

    pages = [
        [{"id": 105}, {"id": 67}, {"id": 100}, {"id": 99}],
        [{"id": 11}, {"id": 22}, {"id": 33}, {"id": 44}],
        [],
    ]
    call_count = 0

    def callback(url:URL, **kwargs):
        nonlocal call_count
        payload = pages[call_count]
        call_count += 1
        return CallbackResult(status=200, payload=payload)


    un = "username"
    url_pattern = re.compile(r"https://danbooru\.donmai\.us/posts\.json.*")

    with aioresponses() as mocked:
        mocked.get(url_pattern, callback=callback, repeat=True)

        async with aiohttp.ClientSession() as session:
            posts = await select_posts(
                database=db,
                session=session,
                mode=DownloadMode.FORCE,
                un=un
            )

    assert call_count == 3
    assert len(mocked.requests) == 3
    post_ids = [p["id"] for p in posts]
    assert post_ids == [105, 67, 100, 99, 11, 22, 33, 44]



