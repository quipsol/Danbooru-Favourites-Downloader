import pytest
from aioresponses import aioresponses

from danbooru_favourites_downloader.main import get_all_new_posts, Context


@pytest.mark.asyncio()
async def test_get_all_new_posts(context: Context):
    url = context.urls.base_url + context.urls.search_result_endpoint
    un = context.environment.account_name

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

        posts = await get_all_new_posts(context=context, latest_id=8)

    assert len(posts) == 7
    assert posts[1]['id'] == 2
    assert 9 not in [p['id'] for p in posts]
