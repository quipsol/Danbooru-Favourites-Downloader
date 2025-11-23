import sqlite3
import os
from dataclasses import dataclass

@dataclass
class PostMetaData:
    post_id: int
    md5: str = ""
    tag_string_general: str = ""
    tag_string_character: str = ""
    tag_string_copyright: str = ""
    tag_string_artist: str = ""
    tag_string_meta: str = ""
    rating: str = ""
    parent_id: int = -1
    has_children: bool = False
    has_active_children: bool = False

    def __init__(self, post_id: int):
        self.post_id = post_id

class Database:
    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()
        self._create_tables()
    
    def _create_tables(self):
        sql_create_table_queries = [ 
        """CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY, 
            md5 TEXT, 
            tag_string_general TEXT,
            tag_string_character TEXT,
            tag_string_copyright TEXT,
            tag_string_artist TEXT,
            tag_string_meta TEXT,
            rating,
            parent_id INTEGER,
            has_children BOOLEAN NOT NULL,
            has_active_children BOOLEAN NOT NULL
        );""",
        """CREATE TABLE IF NOT EXISTS error (
            post_id INTEGER PRIMARY KEY
        );""",
        """CREATE TABLE IF NOT EXISTS key_value_pairs (
            key TEXT PRIMARY KEY,
            value TEXT
        );"""
        ]

        self.cur.execute(sql_create_table_queries[0])
        self.cur.execute(sql_create_table_queries[1])
        self.cur.execute(sql_create_table_queries[2])
        self.con.commit()


    def insert_post_data(self, data:PostMetaData):
        query_data = (data.post_id,
                data.md5,
                data.tag_string_general,
                data.tag_string_character,
                data.tag_string_copyright,
                data.tag_string_artist,
                data.tag_string_meta,
                data.rating,
                data.parent_id,
                data.has_children,
                data.has_active_children)

        query = """INSERT INTO posts (
                    post_id,
                    md5,
                    tag_string_general,
                    tag_string_character,
                    tag_string_copyright,
                    tag_string_artist,
                    tag_string_meta,
                    rating,
                    parent_id,
                    has_children,
                    has_active_children)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)"""
        self.cur.execute(query, query_data)

    def insert_id_to_error(self, id:int):
        query_data = str(id)
        query = """INSERT INTO error (
                    post_id)
                VALUES (?)"""
        self.cur.execute(query, query_data)

    def set_newest_downloaded_id(self, id:int):
        query_data = ("newest_id", str(id))
        query = """INSERT INTO key_value_pairs (key, value)
                        VALUES(?,?)
                        ON CONFLICT (key) DO UPDATE SET value=excluded.value"""
        self.cur.execute(query, query_data)
        self.con.commit()

    def get_newest_downlaoded_id(self) -> int:
        ret = self.cur.execute("SELECT value FROM key_value_pairs WHERE key='newest_id'")
        ret_tuple = ret.fetchone()
        if ret_tuple is None:
            return 0
        else:
            return int(ret_tuple[0])

    def commit(self):
        self.con.commit()

    def close(self):
        self.con.close()