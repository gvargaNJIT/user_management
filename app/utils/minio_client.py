import io
import os
from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

# Initialize the MinIO client
minio_client = Minio(
    "minio:9000",               # Hostname from docker-compose service name
    access_key="minioadmin",
    secret_key="minioadmin123",
    secure=False
)

BUCKET_NAME = "profile-pictures"
DEFAULT_IMAGE_NAME = "DefaultUser.jpg"
DEFAULT_IMAGE_PATH = "settings/DefaultUser.jpg"

def ensure_bucket():
    """
    Ensure the bucket exists in MinIO. Create it if it doesn't.
    """
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)

async def save_image(file_data: bytes, file_name: str) -> str:
    ensure_bucket()
    minio_client.put_object(
        BUCKET_NAME,
        file_name,
        data=io.BytesIO(file_data),
        length=len(file_data),
        content_type="image/jpeg"
    )
    return f"{file_name}"

def get_image(file_name: str) -> io.BytesIO:
    """
    Retrieve an image file from MinIO and return it as a byte stream.
    """
    try:
        image_data = minio_client.get_object(BUCKET_NAME, file_name)
        return io.BytesIO(image_data.read())
    except Exception as e:
        raise Exception(f"Error retrieving image: {str(e)}")

def generate_unique_filename(extension: str) -> str:
    """
    Generate a unique file name using UUID.
    """
    import uuid
    unique_id = uuid.uuid4()
    return f"{unique_id}{extension}"

def upload_default_image_if_missing():
    """
    Upload the default profile picture to MinIO if it's not already there.
    """
    ensure_bucket()
    try:
        # Check if default image exists
        minio_client.stat_object(BUCKET_NAME, DEFAULT_IMAGE_NAME)
    except S3Error as e:
        if e.code == "NoSuchKey":
            # Upload default image
            if not os.path.exists(DEFAULT_IMAGE_PATH):
                raise FileNotFoundError(f"Default profile image not found at {DEFAULT_IMAGE_PATH}")
            minio_client.fput_object(
                BUCKET_NAME,
                DEFAULT_IMAGE_NAME,
                DEFAULT_IMAGE_PATH,
                content_type="image/jpeg"
            )
        else:
            raise

