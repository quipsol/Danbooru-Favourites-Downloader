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
from PIL import Image
import zipfile
import json
import io
from hashlib import md5

class DownloadMode(Enum):
    NORMAL = "normal"
    RETRY  = "retry"
    FORCE  = "force"

load_dotenv()
USERNAME = os.getenv('ACCOUNT_NAME') or ''
API_KEY = os.getenv('API_KEY') or ''
DB_LOCATION = os.getenv('DB_LOCATION') or ''
FILE_DIRECTORY = os.getenv('FILE_DIRECTORY') or ''
CONVERT_UGOIRA_TO_WEBP = (os.getenv('CONVERT_UGOIRA_TO_WEBP') or 'False') == 'True'

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
    file_url = post_json.get('file_url', '')
    if file_url == '':
        print(f"No file url found for post id {post_json['id']}")
        return (False, post_json)
    file_ext = post_json.get('file_ext', '')
    if file_ext == '':
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



async def md5_check(ret:tuple[bool, dict]) -> bool:
    _, post_json = ret
    file_name:str =f'Danbooru_{str(post_json['id'])}'
    file_ext:str = post_json['file_ext']
    path_to_file:str = os.path.join(FILE_DIRECTORY, f'{file_name}.{file_ext}')
    md5_result = md5(open(path_to_file,'rb').read()).hexdigest()
    retVal:bool = post_json['md5'] == md5_result
    if not retVal:
        os.remove(path_to_file)
    return retVal

async def handle_result(ret:tuple[bool, dict], database:Database, mode:DownloadMode):
    success, errors = 0, 0
    donwload_successful, post_json = ret
    post_id = post_json['id']
    if donwload_successful:
        database.insert_post_data(build_metadata(post_json))
        if mode is DownloadMode.RETRY:
            database.remove_from_error(post_id)
            success += 1
    elif mode is not DownloadMode.RETRY:
        database.insert_id_to_error(post_id)
        errors += 1
    return success, errors

async def convert_ugoira_to_webp(ret:tuple[bool, dict]) -> None:
    _, post_json = ret
    file_name:str =f'Danbooru_{str(post_json['id'])}'
    file_ext:str = post_json['file_ext']
    
    path_to_zip:str = os.path.join(FILE_DIRECTORY, f'{file_name}.{file_ext}')
    if path_to_zip.startswith('.'):
        path_to_zip = os.getcwd() + path_to_zip[1:]
    output_file:str = os.path.join(FILE_DIRECTORY, f'{file_name}.webp')
    frames:list[Image.Image] = []
    durations:list[int] | int = []
    frame_files:list[str] = []

    with zipfile.ZipFile(path_to_zip) as zip: # needs absolute path
        meta_file = next((f for f in zip.namelist() if f.endswith(".json")), None)
        
        if meta_file:
            meta = json.loads(zip.read(meta_file))
            frame_files = [f['file'] for f in meta['frames']]
            durations = [f['delay'] for f in meta['frames']]
        else:
            frame_files = sorted(
                f for f in zip.namelist()
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            )
            durations = int(post_json['media_asset'].get('duration', len(frame_files)) * 1000 / len(frame_files))

        for f in frame_files:
            img:Image.Image = Image.open(io.BytesIO(zip.read(f)))
            frames.append(img.convert('RGBA'))

    frames[0].save(
        output_file,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        format='WEBP',
        lossless=True
    )
    os.remove(path_to_zip)



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
                    
                    md5_check_successful = await md5_check(result)
                    if not md5_check_successful:
                        result = (False, result[1])
                    s,e = await handle_result(result, database, mode)
                    if result[0] and result[1]['file_ext'] == 'zip' and CONVERT_UGOIRA_TO_WEBP:
                        await convert_ugoira_to_webp(result)
                    if result[0]:
                        print(f"Finished downloading post with ID {result[1]['id']}")
                    else:
                        print(f"There was an issue downloading post with ID {result[1]['id']}")
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
    if not os.path.exists(DB_LOCATION):
        os.makedirs(DB_LOCATION)
    if not os.path.exists(FILE_DIRECTORY):
        os.makedirs(FILE_DIRECTORY)
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