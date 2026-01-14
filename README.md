# Danbooru Favourites Downloader

This tool downloads every post you have marked as a favourite on your **danbooru.donmai.us** account.
Running it again will automatically download any new favourites added since the last run.

---

## Getting Started

You have **two supported ways** to use this project:

1. **Docker (recommended for developers & technical users)**
2. **Pre-built executables (recommended for non-technical users)**

>Running the raw Python files directly is still possible, but **Docker is now the recommended method**.

---

## Option 1: Using Docker

Docker allows you to run the downloader without installing Python or any dependencies on your system.

### Requirements

* Docker
* Docker Compose

### Setup

1. Clone or download this repository
2. Create a file named **`.env.docker`** in the project root
3. Add the following values to `.env.docker`:

```
ACCOUNT_NAME=your_account_name
API_KEY=your_api_key_here
FILE_DIRECTORY=/downloads
DB_LOCATION=/database
CONVERT_UGOIRA_TO_WEBP=True
```

> **Note**
> Docker uses `.env.docker`.
> The raw Python scripts expect `.env` instead.

### Building the Docker Image

From the project directory, run:

```
docker compose build
```

### Running the Downloader

Run any of the supported modes using Docker Compose:

```
docker compose run danbooru [normal|retry|force]
```

---

## Option 2: Pre-built Executables (No Python/Docker Required)

For users who don't want to run Python or Docker, **pre-packaged executables are available**.

### [Downloads](https://github.com/quipsol/Danbooru-Favourites-Downloader/releases)

Each release provides **three zip files**:

* **Windows**
* **Linux**
* **macOS**

Each zip contains:

* Executables for **all three modes**
* A **pre-made `.env` file** (you must edit this)
* A copy of this **README**

### How to Use

1. Download the zip file for your operating system
2. Extract it anywhere on your system
3. Open the `.env` file and fill in your own values:

   ```
   ACCOUNT_NAME=your_account_name
   API_KEY=your_api_key_here
   FILE_DIRECTORY=path_to_save_files
   DB_LOCATION=path_to_database
   CONVERT_UGOIRA_TO_WEBP=True|False
   ```
4. Run the executable corresponding to the mode you want:

   * danbooru-normal
   * danbooru-retry
   * danbooru-force


---

## Environment Variables

| Variable               | Description                                                  
| ---------------------- | -------------------------------------------------------------
| ACCOUNT_NAME           | Your Danbooru account name                                   
| API_KEY                | Your Danbooru API key                                        
| FILE_DIRECTORY         | Directory where downloaded files will be saved               
| DB_LOCATION            | Directory for the database (can be left empty)               
| CONVERT_UGOIRA_TO_WEBP | Whether to convert Ugoira files to WebP format (True/False).<br> Ugoira are animations stored as images inside a ZIP file. It is recommended to set this to True.

### Getting an API Key

1. Log into Danbooru
2. Go to **My Account**
3. View **API Keys**
4. Create a new key
5. Ensure the following permissions are enabled:

   * `posts:index`
   * `posts:show`
6. Copy the key into your `.env` or `.env.docker` file

---

### Available Modes

* **normal**
  Downloads all favourites on first run, then only new ones on subsequent runs.

* **retry**
  Retries any downloads that previously failed and were logged in the database.

* **force**
  Forces a full re-download of every favourite, even if it already exists.


## Additional Tools

Want to keep Danbooru-style tags and search for your downloaded files?

* [TagStudio](https://docs.tagstud.io/)
* [Danbooru Favourites Downloader → TagStudio Importer](https://github.com/quipsol/DFD-to-TagStudio-importer)
