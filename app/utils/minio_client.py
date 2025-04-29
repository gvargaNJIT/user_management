import io
from fastapi import UploadFile
from minio import Minio

# Directly use credentials or replace these with environment variables if needed
minio_client = Minio(
    "minio:9000",               # Hostname from docker-compose service name
    access_key="minioadmin",
    secret_key="minioadmin123",
    secure=False
)

BUCKET_NAME = "profile-pictures"

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
    return f"{BUCKET_NAME}/{file_name}"

def get_image(file_name: str) -> io.BytesIO:
    """
    Retrieve an image file from MinIO and return it as a byte stream.

    Args:
        file_name: The file name of the image to retrieve.
    
    Returns:
        io.BytesIO: The image file content as a byte stream.
    """
    try:
        # Get the object from MinIO storage
        image_data = minio_client.get_object(BUCKET_NAME, file_name)
        # Return the image data as a BytesIO stream
        return io.BytesIO(image_data.read())
    except Exception as e:
        raise Exception(f"Error retrieving image: {str(e)}")

def generate_unique_filename(extension: str) -> str:
    """
    Generate a unique file name using UUID.

    Args:
        extension: The file extension (e.g., .jpg, .png).
    
    Returns:
        str: The unique file name.
    """
    import uuid
    unique_id = uuid.uuid4()  # Generates a unique UUID
    return f"{unique_id}{extension}"
