# Danbooru Favourites Downloader

This tool downloads every post you marked as favourite on your danbooru.donmai.us account. Running it again will download any new favourites.


# Download

Download the project files and install the required dependencies


1. Download files
2. Install python from [Python.org](https://www.python.org)
3. run this command from the projects directory

       py -m pip install -r requirements.txt

# Setup

1. Create a ".env" file in the directory
2. Add the following keys and values to your .env file

    - FILE_DIRECTORY = Path in which the files will be saved in
    - DB_LOCATION = Path in which to save the database (can be left empty)
    - ACCOUNT_NAME = Your danbooru.donmai.us account name
    - API_KEY = 
        1. Log into your Danbooru account.
        2. Go to "My Account" and View your API Keys.
        3. Create a new key and Edit it.
        4. Choose the permissions for this key (default is ALL)

            Required permissions: *posts:index* & *posts:show*

        5. Copy the key into your .env file

Example .env file:

    FILE_DIRECTORY=C:/Danbooru/Downloads
    DB_LOCATION=./Database
    ACCOUNT_NAME=account_name
    API_KEY=abc123DEF456DdeLxyZ

# Running the program

Run any of the relevant python files

- **download_posts**: Downloads any new posts that you favourited (or all on first run)
- **retry_downloading_failures**: If there was an issue with any download it will be logged in the database. This will retry downloading those files.
- **redownload_everything**: Will redownload every single file, no matter if it has been downloaded before already.

***

Want to keep the tags and search functionality of the danbooru website? Check out [TagStudio](https://docs.tagstud.io/) and this tag import tool [Danbooru-Favourites-Downloader to TagStudio Importer](https://github.com/quipsol/DFD-into-TagStudio-importer)