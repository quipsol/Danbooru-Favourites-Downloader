import pytest
import aiohttp
from aioresponses import aioresponses

from danbooru_favourites_downloader.main import get_all_new_posts


@pytest.mark.asyncio()
async def test_get_all_new_posts():
    url = r"https://danbooru.donmai.us/posts.json"
    un = "username"
    with aioresponses() as m:
        m.get(
            f"{url}?tags=ordfav:{un}&limit=20&page=1",
            payload=[{"id": 1, "other": 99}, {"id": 2, "other": 99}, {"id": 3, "other": 99}]
        )
        m.get(
             f"{url}?tags=ordfav:{un}&limit=20&page=2",
             payload=[{"id": 4}, {"id": 5},{"id": 6}]
        )
        m.get(
            f"{url}?tags=ordfav:{un}&limit=20&page=3",
            payload=[{"id": 7}, {"id": 8},{"id": 9}]
        )

        async with aiohttp.ClientSession() as session:
            posts = await get_all_new_posts(session=session, auth=None, latest_id=8, un=un)

    assert len(posts) == 7
    assert posts[1]['id'] == 2
    assert 9 not in [p['id'] for p in posts]
