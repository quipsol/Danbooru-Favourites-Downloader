from danbooru_favourites_downloader.main import build_metadata

def test_build_metadata():
    post = {
        "id": 123,
        "md5": "SADbjf5349bg78D",
        "tag_string_general": "tag1 tag2",
        "tag_string_character": "",
        "tag_string_copyright": "",
        "tag_string_artist": "",
        "tag_string_meta": "",
        "rating": "g",
        "parent_id": None,
        "has_children": False,
        "has_active_children": False,
        "file_ext": "jpg",
    }

    meta = build_metadata(post)

    assert meta.post_id == 123, f"Expected value: 123, got: {meta.post_id}"
    assert meta.md5 == "SADbjf5349bg78D", f"Expected value: SADbjf5349bg78D, got: {meta.md5}"
    assert meta.file_ext == "jpg", f"Expected value: jpg, got: {meta.file_ext}"
    assert meta.rating == "g", f"Expected value: g, got: {meta.rating}"
