
from sys import exit as sys_exit
import os

from database import Database, PostMetaData

from pybooru import Danbooru
from dotenv import load_dotenv
import asyncio
import aiohttp
from alive_progress import alive_bar

load_dotenv()
USERNAME = os.getenv('ACCOUNT_USERNAME')
API_KEY = os.getenv('API_KEY')
DB_LOCATION = os.getenv('DB_LOCATION')
FILE_DIRECTORY = os.getenv('FILE_DIRECTORY')

if DB_LOCATION is None or FILE_DIRECTORY is None or USERNAME is None or API_KEY is None:
    print('Please set the neccessary values in your .env file')
    sys_exit(0)

client = Danbooru('danbooru', username=USERNAME, api_key=API_KEY)
database = Database(os.path.join(DB_LOCATION, "post-downloads.db"))
ordfav_tag = 'ordfav:' + USERNAME


async def download_file(post_json: dict, session) -> tuple[bool, dict]:
    file_url = post_json.get('file_url')
    if not file_url:
        print(f"No file url found for post id {post_json['id']}")
        return [False, post_json]
    file_ext = post_json.get('file_ext')
    if not file_ext:
        print(f"No original variant found for post id {post_json['id']}")
        return [False, post_json]

    async with session.get(file_url) as resp:
        resp.raise_for_status()
        file_name = f"Danbooru_{str(post_json['id'])}.{file_ext}"
        complete_path = os.path.join(FILE_DIRECTORY, file_name)

        with open(complete_path, "wb") as f:
            async for chunk in resp.content.iter_chunked(8192):
                f.write(chunk)
    return [True, post_json]


 
def get_specific_favourites_page_posts(page: int = 1) -> list:
    # ! Limit is ALSO the page size! so "limit=5, page=2" will yield posts 6-10!
    return client.post_list(limit=20, page=page, tags=ordfav_tag)



def get_all_new_posts(latest_id: int) -> list:
    page = 1
    final_result = []
    while True:
        result = get_specific_favourites_page_posts(page)
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
        


async def a_main():
    print('Looking for new IDs')

    latest_id = database.get_newest_downlaoded_id()
    
    posts_response = get_all_new_posts(latest_id)
    post_ids = [item['id'] for item in posts_response]
    if len(post_ids) == 0:
        print('No new IDs')
        database.close()
        return
    print(f"{str(len(post_ids))} new IDs found")
    newest_id = post_ids[0]
    print('Beginning to download posts...')
    errors = 0
    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(download_file(post, session))
            for post in posts_response
        ]
        total = len(tasks)
        with alive_bar(total, title="Downloading posts") as bar:
            for completed_task in asyncio.as_completed(tasks):
                ret = await completed_task
                post_dict = ret[1]
                post_id = post_dict['id']
                if ret[0]:
                    pmd = PostMetaData(post_id)
                    pmd.md5 =post_dict['md5']
                    pmd.tag_string_general = post_dict['tag_string_general']
                    pmd.tag_string_character = post_dict['tag_string_character']
                    pmd.tag_string_copyright = post_dict['tag_string_copyright']
                    pmd.tag_string_artist = post_dict['tag_string_artist']
                    pmd.tag_string_meta = post_dict['tag_string_meta']
                    pmd.rating = post_dict['rating']
                    pmd.parent_id = post_dict['parent_id']
                    pmd.has_children = post_dict['has_children']
                    pmd.has_active_children = post_dict['has_active_children']
                    if pmd.has_children is None:
                        pmd.has_children = False
                    if pmd.has_active_children is None:
                        pmd.has_active_children = False
                    database.insert_post_data(pmd)
                else:
                    errors += 1
                    data = (post_id)
                    database.insert_id_to_error(post_id)
                bar()
                print(f"Finished downloading post with ID {post_id}")
    if errors > 0:
        print(f"Failed to download {errors} IDs!")

    database.set_newest_downloaded_id(newest_id)
    database.commit()
    database.close()
    print('Done')
    


def main():
    asyncio.run(a_main())




if __name__ == "__main__":
    main()