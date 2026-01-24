import aiohttp
import pytest



@pytest.mark.asyncio()
@pytest.mark.parametrize(
    "url, params",
    [
        (
            "https://danbooru.donmai.us/posts.json",
            {
            'limit': 20,
            'page': 1
            },          
        ),
        (
            "https://danbooru.donmai.us/posts/9627266.json",
            { },
        ),
    ],
)
async def test_api_json_response_content(url, params):
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            result = await resp.json()
            if type(result) is list:
                data = result[0]
            else: #type should be dict
                data = result
    
    assert "id" in data
    assert "md5" in data
    assert "tag_string_general" in data
    assert "tag_string_copyright" in data
    assert "tag_string_artist" in data
    assert "tag_string_meta" in data
    assert "rating" in data
    assert "parent_id" in data
    assert "has_children" in data
    assert "has_active_children" in data
    assert "file_ext" in data
    assert "duration" in data['media_asset']