import os
from supabase import create_client, Client

SUPABASE_URL = "https://xnuadageyjmxurcbduie.supabase.co"
SUPABASE_KEY = "sb_secret_s_082ip6RyNkIvhd_bZfWA_k-lYWN4f"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

file_path = "storage/mappa_20260204_202404_1.jpg"

def upload():
    with open(file_path, "rb") as f:
        response = supabase.storage.from_("images").upload(
            path="uploads/mappa_20260204_202404_1.jpg",
            file=f,
            file_options={"content-type": "image/jpeg"}
        )

    print(response)

    public_url = supabase.storage.from_("images").get_public_url("uploads/mappa_20260204_202404_1.jpg")
    print(public_url)

def delete():
    response = supabase.storage.from_("images").remove([path])

    print(response)

