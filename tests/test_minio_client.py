import io
import os
import pytest
from unittest.mock import patch, MagicMock
from minio.error import S3Error

# Import the entire module (to allow proper patching)
import app.utils.minio_client as minio_module

# Aliases to avoid rebinding and allow patching to take effect
ensure_bucket = minio_module.ensure_bucket
save_image = minio_module.save_image
get_image = minio_module.get_image
upload_default_image_if_missing = minio_module.upload_default_image_if_missing

BUCKET_NAME = minio_module.BUCKET_NAME
DEFAULT_IMAGE_NAME = minio_module.DEFAULT_IMAGE_NAME
DEFAULT_IMAGE_PATH = minio_module.DEFAULT_IMAGE_PATH


@pytest.fixture
def mock_minio_client():
    """Fixture to patch minio_client inside the actual module under test."""
    with patch('app.utils.minio_client.minio_client') as mock_client:
        yield mock_client


class TestMinioStorage:
    """Test the MinIO storage functionality."""

    def test_ensure_bucket_exists(self, mock_minio_client):
        mock_minio_client.bucket_exists.return_value = True
        ensure_bucket()
        mock_minio_client.bucket_exists.assert_called_once_with(BUCKET_NAME)
        mock_minio_client.make_bucket.assert_not_called()

    def test_ensure_bucket_not_exists(self, mock_minio_client):
        mock_minio_client.bucket_exists.return_value = False
        ensure_bucket()
        mock_minio_client.bucket_exists.assert_called_once_with(BUCKET_NAME)
        mock_minio_client.make_bucket.assert_called_once_with(BUCKET_NAME)

    @pytest.mark.asyncio
    async def test_save_image(self, mock_minio_client):
        file_data = b"test image data"
        file_name = "test_image.jpg"

        result = await save_image(file_data, file_name)

        assert mock_minio_client.put_object.called
        args, kwargs = mock_minio_client.put_object.call_args

        assert args[0] == BUCKET_NAME
        assert args[1] == file_name
        assert isinstance(kwargs["data"], io.BytesIO)
        assert kwargs["length"] == len(file_data)
        assert kwargs["content_type"] == "image/jpeg"
        assert result == file_name

    def test_get_image_success(self, mock_minio_client):
        file_name = "existing_image.jpg"
        mock_response = MagicMock()
        mock_response.read.return_value = b"test image data"
        mock_minio_client.get_object.return_value = mock_response

        result = get_image(file_name)
        mock_minio_client.get_object.assert_called_once_with(BUCKET_NAME, file_name)
        assert isinstance(result, io.BytesIO)
        assert result.getvalue() == b"test image data"

    def test_get_image_not_found(self, mock_minio_client):
        file_name = "non_existing_image.jpg"
        mock_error = S3Error(
            code="NoSuchKey",
            message="The specified key does not exist",
            resource=f"{BUCKET_NAME}/{file_name}",
            request_id="req-id",
            host_id="host-id",
            response=MagicMock()
        )
        mock_minio_client.get_object.side_effect = mock_error

        with pytest.raises(S3Error):
            get_image(file_name)

        mock_minio_client.get_object.assert_called_once_with(BUCKET_NAME, file_name)

    def test_upload_default_image_already_exists(self, mock_minio_client):
        mock_minio_client.stat_object.return_value = MagicMock()
        upload_default_image_if_missing()
        mock_minio_client.stat_object.assert_called_once_with(BUCKET_NAME, DEFAULT_IMAGE_NAME)
        mock_minio_client.fput_object.assert_not_called()

    @patch('os.path.exists')
    def test_upload_default_image_missing_uploads_file(self, mock_exists, mock_minio_client):
        mock_error = S3Error(
            code="NoSuchKey",
            message="The specified key does not exist",
            resource=f"{BUCKET_NAME}/{DEFAULT_IMAGE_NAME}",
            request_id="req-id",
            host_id="host-id",
            response=MagicMock()
        )
        mock_minio_client.stat_object.side_effect = mock_error
        mock_exists.return_value = True

        upload_default_image_if_missing()

        mock_minio_client.stat_object.assert_called_once_with(BUCKET_NAME, DEFAULT_IMAGE_NAME)
        mock_minio_client.fput_object.assert_called_once_with(
            BUCKET_NAME,
            DEFAULT_IMAGE_NAME,
            DEFAULT_IMAGE_PATH,
            content_type="image/jpeg"
        )

    @patch('os.path.exists')
    def test_upload_default_image_missing_file_not_found(self, mock_exists, mock_minio_client):
        mock_error = S3Error(
            code="NoSuchKey",
            message="The specified key does not exist",
            resource=f"{BUCKET_NAME}/{DEFAULT_IMAGE_NAME}",
            request_id="req-id",
            host_id="host-id",
            response=MagicMock()
        )
        mock_minio_client.stat_object.side_effect = mock_error
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            upload_default_image_if_missing()

        mock_minio_client.stat_object.assert_called_once_with(BUCKET_NAME, DEFAULT_IMAGE_NAME)
        mock_minio_client.fput_object.assert_not_called()

    def test_upload_default_image_other_s3_error(self, mock_minio_client):
        mock_error = S3Error(
            code="SomeOtherError",
            message="Some other error occurred",
            resource=f"{BUCKET_NAME}/{DEFAULT_IMAGE_NAME}",
            request_id="req-id",
            host_id="host-id",
            response=MagicMock()
        )
        mock_minio_client.stat_object.side_effect = mock_error

        with pytest.raises(S3Error):
            upload_default_image_if_missing()

        mock_minio_client.stat_object.assert_called_once_with(BUCKET_NAME, DEFAULT_IMAGE_NAME)
        mock_minio_client.fput_object.assert_not_called()
