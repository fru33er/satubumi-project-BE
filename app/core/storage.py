import os

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    secret_key = os.getenv("SUPABASE_SECRET_KEY")

    if not url:
        raise RuntimeError(
            "SUPABASE_URL belum dikonfigurasi."
        )

    if not secret_key:
        raise RuntimeError(
            "SUPABASE_SECRET_KEY belum dikonfigurasi."
        )

    return create_client(
        url,
        secret_key,
    )


def get_public_bucket() -> str:
    return os.getenv(
        "SUPABASE_PUBLIC_BUCKET",
        "satubumi-public",
    )


def upload_public_file(
    path: str,
    file_bytes: bytes,
    content_type: str,
) -> str:
    supabase = get_supabase_client()
    bucket = get_public_bucket()

    supabase.storage.from_(bucket).upload(
        path=path,
        file=file_bytes,
        file_options={
            "content-type": content_type,
            "cache-control": "3600",
            "upsert": "false",
        },
    )

    public_url = (
        supabase.storage
        .from_(bucket)
        .get_public_url(path)
    )

    return public_url


def delete_public_file(
    path: str,
) -> None:
    supabase = get_supabase_client()
    bucket = get_public_bucket()

    supabase.storage.from_(bucket).remove(
        [path]
    )


def extract_public_storage_path(
    file_url: str | None,
) -> str | None:
    if not file_url:
        return None

    bucket = get_public_bucket()

    marker = (
        f"/storage/v1/object/public/"
        f"{bucket}/"
    )

    if marker not in file_url:
        return None

    return file_url.split(
        marker,
        1,
    )[1]