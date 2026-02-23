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

    database = Database(":memory:")
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
    database.close()
    await session.close()