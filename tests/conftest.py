import pytest
import pytest_asyncio
import asyncio
import aiohttp
from unittest.mock import Mock, create_autospec

from danbooru_favourites_downloader.main import DownloadMode, Environment, Urls, Context
from danbooru_favourites_downloader.database import Database

@pytest_asyncio.fixture
async def context():

    env = Environment(
        account_name="testAccount",
        api_key="apiKey",
        db_location=":memory:",
        file_directory="/tmp",
        convert_ugoira_to_webp=True,
    )
    urls = Urls(
        base_url="https://danbooru.donmai.us",
        search_result_endpoint="/posts.json",
        specific_post_endpoint="/posts/{0}.json",
    )

    database = create_autospec(Database, instance=True)
    session = aiohttp.ClientSession()
    authenticator = aiohttp.BasicAuth(login=env.account_name, password=env.api_key)

    ctx = Context(
        environment=env,
        database=database,
        session=session,
        mode=DownloadMode.NORMAL,
        authenticator=authenticator,
        urls=urls,
        rate_limit_interval=1.0,
        semaphore=asyncio.Semaphore(10),
    )
    
    yield ctx

    await session.close()



@pytest.fixture
def context_factory():
    def _create(**overrides):
        env = Environment(
            account_name="testAccount",
            api_key="apiKey",
            db_location=":memory:",
            file_directory="/tmp",
            convert_ugoira_to_webp=True,
        )

        urls = Urls(
            base_url="https://danbooru.donmai.us",
            search_result_endpoint="/posts.json",
            specific_post_endpoint="/posts/{0}.json",
        )

        ctx = Context(
            environment=env,
            database=Mock(),
            session=Mock(spec=aiohttp.ClientSession),
            mode=DownloadMode.NORMAL,
            authenticator=Mock(),
            urls=urls,
            rate_limit_interval=1.0,
            semaphore=asyncio.Semaphore(10),
        )

        for key, value in overrides.items():
            setattr(ctx, key, value)

        return ctx

    return _create