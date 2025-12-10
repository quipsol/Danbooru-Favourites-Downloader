
from sys import exit as sys_exit
from sys import argv
import os
from database import Database, PostMetaData
from pybooru import Danbooru, exceptions as booru_exc
from dotenv import load_dotenv
import asyncio
import aiohttp
from alive_progress import alive_bar
from time import sleep, time
from enum import Enum, auto

class DownloadMode(Enum):
    NORMAL = auto()
    RETRY  = auto()
    FORCE  = auto()

load_dotenv()
USERNAME = os.getenv('ACCOUNT_NAME')
API_KEY = os.getenv('API_KEY')
DB_LOCATION = os.getenv('DB_LOCATION')
FILE_DIRECTORY = os.getenv('FILE_DIRECTORY')

if DB_LOCATION is None or FILE_DIRECTORY is None or USERNAME is None or API_KEY is None:
    print("Please set the following values in your .env file")
    if USERNAME is None: print("ACCOUNT_NAME")
    if API_KEY is None: print("API_KEY")
    if DB_LOCATION is None: print("DB_LOCATION")
    if FILE_DIRECTORY is None: print("FILE_DIRECTORY")
    sys_exit(0)

client = Danbooru('danbooru', username=USERNAME, api_key=API_KEY)



def get_all_error_posts(database:Database)-> list[dict]:
    error_ids = database.get_error_ids()
    if len(error_ids) == 0:
        return []
    posts = []
    for id in error_ids:
        start = time()
        posts.append(client.post_show(id))
        sleep(max(0, 0.105-(time() - start))) # rate limit of 10/s
    return posts

def get_all_new_posts(latest_id: int = 0) -> list[dict]:
    page = 1
    final_result = []
    while True:
        start = time()
        result = client.post_list(limit=20, page=page, tags=f"ordfav:{USERNAME}")
        sleep(max(0, 0.105-(time() - start))) # rate limit of 10/s
        if result == []:
            break
        result_ids = [item['id'] for item in result]
        if latest_id in result_ids:
            stop_index = result_ids.index(latest_id)
            final_result.extend(result[:stop_index])
            break
        final_result.extend(result)
        page += 1
    return final_result
        
def select_posts(database:Database, mode:DownloadMode)->list[dict]:
    if mode is DownloadMode.NORMAL:
        return get_all_new_posts(database.get_newest_downlaoded_id())
    elif mode is DownloadMode.RETRY:
        print("Gathering IDs of posts that failed to download before")
        return get_all_error_posts(database)
    else:
        return get_all_new_posts(database.get_newest_downlaoded_id())


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
    pmd.has_children = post.get('has_children') or False
    pmd.has_active_children = post.get('has_active_children') or False
    pmd.file_ext = post['file_ext']
    if pmd.has_children is None:
        pmd.has_children = False
    if pmd.has_active_children is None:
        pmd.has_active_children = False
    return pmd

semaphore = asyncio.Semaphore(10)
async def download_limited(post_json: dict, session):
    async with semaphore:
        return await download_file(post_json, session)

async def download_file(post_json: dict, session) -> tuple[bool, dict]:
    file_url = post_json.get('file_url')
    if not file_url:
        print(f"No file url found for post id {post_json['id']}")
        return [False, post_json]
    file_ext = post_json.get('file_ext')
    if not file_ext:
        print(f"No original variant found for post id {post_json['id']}")
        return [False, post_json]
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
        return [False, post_json]
    return [True, post_json]

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

        posts = select_posts(database, mode)
        post_ids = [p['id'] for p in posts]
        if not post_ids:
            if mode is DownloadMode.RETRY: print("No post marked as a failed download")
            else: print("No new IDs found")
            return
        print(f"{str(len(post_ids))} new IDs found")
        
        total_success = total_errors = 0
        newest_id = post_ids[0]
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(download_limited(post, session)) for post in posts]

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
    print('Done')
    sleep(3)
    


def main(mode:DownloadMode = DownloadMode.NORMAL):
    asyncio.run(a_main(mode))

if __name__ == "__main__":
    main(DownloadMode.NORMAL)