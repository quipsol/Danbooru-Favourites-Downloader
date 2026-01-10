
from sys import exit as sys_exit
from sys import argv as sys_argv
import os
from database import Database, PostMetaData
from dotenv import load_dotenv
import asyncio
import aiohttp
from alive_progress import alive_bar
from time import sleep, time
from enum import Enum, auto

class DownloadMode(Enum):
    NORMAL = "normal"
    RETRY  = "retry"
    FORCE  = "force"

load_dotenv()
USERNAME = os.getenv('ACCOUNT_NAME') or ''
API_KEY = os.getenv('API_KEY') or ''
DB_LOCATION = os.getenv('DB_LOCATION') or ''
FILE_DIRECTORY = os.getenv('FILE_DIRECTORY') or ''

if FILE_DIRECTORY == '' or USERNAME == '' or API_KEY == '':
    print("Please set the following values in your .env file")
    if USERNAME == '': print("ACCOUNT_NAME")
    if API_KEY == '': print("API_KEY")
    if FILE_DIRECTORY == '': print("FILE_DIRECTORY")
    sys_exit(0)



if DB_LOCATION is None:
    DB_LOCATION = os.getcwd()

RATE_LIMIT_INTERVAL = 1.0 # only 1 request per second
semaphore = asyncio.Semaphore(10)
authenticator = aiohttp.BasicAuth(login=USERNAME, password=API_KEY)
base_url = 'https://danbooru.donmai.us'
search_result_endpoint = '/posts.json' # needs post:index key access
specific_post_endpoint = '/posts/{0}.json' # needs post:show key access


async def get_all_error_posts(session:aiohttp.ClientSession, database:Database)-> list[dict]:
    error_ids = database.get_error_ids()
    if len(error_ids) == 0:
        return []
    posts = []
    end = 0
    for id in error_ids:
        start = time()
        async with session.get(base_url + specific_post_endpoint.format(id), auth=authenticator) as resp:
            resp.raise_for_status()
            posts.append(await resp.json())
        if len(posts) > 100: # Make use of burst pool
            await asyncio.sleep(max(0, RATE_LIMIT_INTERVAL - (time() - start))) # 1 request per second
    return posts

async def get_all_new_posts(session:aiohttp.ClientSession, latest_id: int = 0) -> list[dict]:
    page = 1
    final_result = []
    end = 0
    while True:
        start = time()
        params = {
            'tags': f'ordfav:{USERNAME}',
            'limit': 20,
            'page': page
        }
        async with session.get(base_url + search_result_endpoint, params=params, auth=authenticator) as resp:
            resp.raise_for_status()
            result = await resp.json()

        if result == []:
            break
        result_ids = [item['id'] for item in result]
        if latest_id in result_ids:
            stop_index = result_ids.index(latest_id)
            final_result.extend(result[:stop_index])
            break
        final_result.extend(result)
        page += 1
        if page > 100: # Make use of burst pool
            await asyncio.sleep(max(0, RATE_LIMIT_INTERVAL - (time() - start))) # Max 1 request per second
    return final_result
        
async def select_posts(database:Database, session, mode:DownloadMode)->list[dict]:
    if mode is DownloadMode.NORMAL:
        return await get_all_new_posts(session, database.get_newest_downlaoded_id())
    elif mode is DownloadMode.RETRY:
        print("Gathering IDs of posts that failed to download before")
        return await get_all_error_posts(session, database)
    else: # DownloadMode.FORCE
        return await get_all_new_posts(session)



def build_metadata(post: dict) -> PostMetaData:
    pmd = PostMetaData(post['id'])
    pmd.md5 = post['md5']
    pmd.tag_string_general = post['tag_string_general']
    pmd.tag_string_character = post['tag_string_character']
    pmd.tag_string_copyright = post['tag_string_copyright']
    pmd.tag_string_artist = post['tag_string_artist']
    pmd.tag_string_meta = post['tag_string_meta']
    pmd.rating = post['rating']
    pmd.parent_id = post['parent_id']
    pmd.has_children = bool(post.get('has_children'))
    pmd.has_active_children = bool(post.get('has_active_children'))
    pmd.file_ext = post['file_ext']
    return pmd

async def download_limiter(session:aiohttp.ClientSession, post_json: dict):
    async with semaphore:
        return await download_file(session, post_json)

async def download_file(session:aiohttp.ClientSession, post_json: dict) -> tuple[bool, dict]:
    file_url = post_json.get('file_url')
    if not file_url:
        print(f"No file url found for post id {post_json['id']}")
        return (False, post_json)
    file_ext = post_json.get('file_ext')
    if not file_ext:
        print(f"No original variant found for post id {post_json['id']}")
        return (False, post_json)
    try:
        async with session.get(file_url) as resp:
            resp.raise_for_status()
            file_name = f"Danbooru_{str(post_json['id'])}.{file_ext}"
            complete_path = os.path.join(FILE_DIRECTORY, file_name)

            with open(complete_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(8192):
                    f.write(chunk)
    except Exception as e:
        print(f"[EXCEPTION] Download failed with error: {e}")
        return (False, post_json)
    return (True, post_json)

def handle_result(ret:tuple[bool, dict], database:Database, mode:DownloadMode):
    success, errors = 0, 0
    ok, post = ret
    post_id = post['id']
    if ok:
        database.insert_post_data(build_metadata(post))
        if mode is DownloadMode.RETRY:
            database.remove_from_error(post_id)
            success += 1
    elif mode is not DownloadMode.RETRY:
        database.insert_id_to_error(post_id)
        errors += 1
    return success, errors



async def a_main(mode: DownloadMode):
    with Database(os.path.join(DB_LOCATION, "post-downloads.db")) as database:
        if mode is DownloadMode.FORCE:
            database.delete_tables()
            database.create_tables()
            database.commit()
        
        async with aiohttp.ClientSession() as session:
            posts = await select_posts(database, session, mode)
            post_ids = [p['id'] for p in posts]
            if not post_ids:
                if mode is DownloadMode.RETRY: print("No post marked as a failed download")
                else: print("No new IDs found")
                return
            print(f"{str(len(post_ids))} new IDs found")

            total_success = total_errors = 0
            newest_id = post_ids[0]

            tasks = [asyncio.create_task(download_limiter(session, post)) for post in posts]

            with alive_bar(len(tasks), title="Downloading posts") as bar:
                for completed_task in asyncio.as_completed(tasks):
                    result = await completed_task
                    print(f"Finished downloading post with ID {result[1]['id']}")
                    s,e = handle_result(result, database, mode)
                    total_success += s
                    total_errors += e
                    bar()

        if total_errors > 0: print(f"Failed to download {total_errors} IDs!")
        if total_success > 0: print(f"Successfully downloaded {total_success} IDs!")
        if mode is not DownloadMode.RETRY:
            database.set_newest_downloaded_id(newest_id)

        database.commit()
    print("Done")
    sleep(2)

def main(mode:DownloadMode = DownloadMode.NORMAL):
    asyncio.run(a_main(mode))

if __name__ == "__main__":
    if len(sys_argv) > 1 and sys_argv[1] in ("-h", "--help"):
        print("Usage: danbooru [normal|retry|force]")
        sys_exit(0)

    mode:DownloadMode = DownloadMode.NORMAL
    if len(sys_argv) == 2:
        arg = sys_argv[1].lower()
        try:
            mode = DownloadMode(arg)
        except ValueError:
            raise SystemExit(
                f"Unknown mode '{arg}'. "
                f"Valid modes: normal, retry, force"
            )
    main(mode)