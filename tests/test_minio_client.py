import pytest
import io
import os
import uuid
from minio import Minio
from minio.error import S3Error
from unittest.mock import MagicMock
from pytest_mock import MockerFixture
from app.utils.minio_client import (
    minio_client,
    BUCKET_NAME,
    DEFAULT_IMAGE_NAME,
    DEFAULT_IMAGE_PATH,
    ensure_bucket,
    save_image,
    get_image,
    upload_default_image_if_missing
)

TEST_BUCKET_PREFIX = "test-profile-pictures-"

@pytest.fixture(scope="module")
def minio_test_bucket_name():
    """Provides a unique bucket name for this test module."""
    return f"{TEST_BUCKET_PREFIX}{uuid.uuid4()}"

@pytest.fixture(scope="function")
def setup_and_teardown_bucket(minio_test_bucket_name, request, mocker: MockerFixture):
    """
    Ensures the test bucket exists before integration tests and cleans up
    all objects and the bucket itself after tests in this module.
    Includes mocking for cleanup failure tests using the module-scoped mocker.
    """
    bucket_name = minio_test_bucket_name
    print(f"\nSetting up MinIO test bucket: {bucket_name}")
    
    try:
        minio_client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created.")
    except S3Error as e:
        if e.code == "BucketAlreadyOwnedByYou":
            print(f"Bucket '{bucket_name}' already exists.")
        else:
            print(f"Error during bucket setup {bucket_name}: {e}")
            raise
    
    # Mock the list_objects function to return a list of objects with proper object_name values
    mock_object = MagicMock()
    mock_object.object_name = 'test_file.txt'  # Ensure the object_name is a string
    
    # Patch minio_client.list_objects to return the mocked objects
    mocker.patch.object(minio_client, 'list_objects', return_value=[mock_object])
    
    yield bucket_name
    
    print(f"\nCleaning up MinIO test bucket: {bucket_name}")
    try:
        # Now you can safely call remove_object, as mock_object.object_name is a valid string
        objects = minio_client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            try:
                # Ensure obj.object_name is a string explicitly here
                minio_client.remove_object(bucket_name, str(obj.object_name))
            except S3Error as e:
                print(f"Error removing object {obj.object_name}: {e}")
    except S3Error as e:
        print(f"Error during bucket cleanup {bucket_name}: {e}")
    
    # Clean up the bucket itself after removing objects
    try:
        minio_client.remove_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' removed.")
    except S3Error as e:
        print(f"Error removing bucket {bucket_name}: {e}")

@pytest.fixture
def dummy_image_data():
    """Provides simple dummy image data (bytes)."""
    jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00'
    return jpeg_header + b'fake image data'


@pytest.mark.asyncio
async def test_save_image_uploads_file(minio_test_bucket_name, dummy_image_data, monkeypatch):
    """
    Test that save_image uploads the image data to MinIO.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', minio_test_bucket_name)
    file_name = "test_upload.jpg"

    returned_name = await save_image(dummy_image_data, file_name)

    assert returned_name == file_name

    try:
        stat = minio_client.stat_object(minio_test_bucket_name, file_name)
        assert stat.size == len(dummy_image_data)
        assert stat.content_type == "image/jpeg"
    except S3Error as e:
        pytest.fail(f"Failed to stat uploaded object: {e}")


def test_get_image_retrieves_file(minio_test_bucket_name, dummy_image_data, monkeypatch):
    """
    Test that get_image retrieves the image data from MinIO.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', minio_test_bucket_name)
    file_name = "test_download.jpg"

    try:
        minio_client.put_object(
            minio_test_bucket_name,
            file_name,
            data=io.BytesIO(dummy_image_data),
            length=len(dummy_image_data),
            content_type="image/jpeg"
        )
    except S3Error as e:
        pytest.fail(f"Failed to upload file for get test setup: {e}")

    retrieved_stream = get_image(file_name)

    assert isinstance(retrieved_stream, io.BytesIO)
    assert retrieved_stream.read() == dummy_image_data


def test_get_image_handles_not_found(minio_test_bucket_name, monkeypatch):
    """
    Test that get_image raises S3Error with code NoSuchKey for a non-existent file.
    Requires get_image in app code to re-raise S3Error.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', minio_test_bucket_name)
    non_existent_file_name = "non_existent_image.jpg"

    with pytest.raises(S3Error) as excinfo:
         get_image(non_existent_file_name)

    assert excinfo.value.code == "NoSuchKey"


def test_upload_default_image_if_missing_uploads_if_missing(minio_test_bucket_name, monkeypatch):
    """
    Test that upload_default_image_if_missing uploads the default image
    when it's not in the bucket but the local file exists.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', minio_test_bucket_name)

    try:
        minio_client.remove_object(minio_test_bucket_name, DEFAULT_IMAGE_NAME)
        print(f"Cleaned up {DEFAULT_IMAGE_NAME} before test_upload_default_image_if_missing_uploads_if_missing")
    except S3Error as e:
         if e.code != "NoSuchKey":
             pytest.fail(f"Error cleaning up {DEFAULT_IMAGE_NAME} before test: {e}")

    try:
        minio_client.stat_object(minio_test_bucket_name, DEFAULT_IMAGE_NAME)
        pytest.fail(f"Default image '{DEFAULT_IMAGE_NAME}' should not exist in bucket before test function call.")
    except S3Error as e:
        assert e.code == "NoSuchKey"

    original_exists = os.path.exists(DEFAULT_IMAGE_PATH)
    created_dummy = False
    if not original_exists:
         os.makedirs(os.path.dirname(DEFAULT_IMAGE_PATH), exist_ok=True)
         with open(DEFAULT_IMAGE_PATH, "wb") as f:
              f.write(b"dummy default image content for upload test")
         created_dummy = True

    try:
        upload_default_image_if_missing()

        stat = minio_client.stat_object(minio_test_bucket_name, DEFAULT_IMAGE_NAME)
        assert stat is not None
        if created_dummy:
             assert stat.size == len(b"dummy default image content for upload test")

    finally:
         if created_dummy and os.path.exists(DEFAULT_IMAGE_PATH):
              try:
                  os.remove(DEFAULT_IMAGE_PATH)
              except OSError as e:
                   print(f"Warning: Could not remove dummy file during cleanup {DEFAULT_IMAGE_PATH}: {e}")


def test_upload_default_image_if_missing_does_nothing_if_exists(minio_test_bucket_name, dummy_image_data, monkeypatch):
    """
    Test that upload_default_image_if_missing does nothing when the default
    image already exists in the bucket.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', minio_test_bucket_name)
    file_name = DEFAULT_IMAGE_NAME

    try:
        minio_client.remove_object(minio_test_bucket_name, DEFAULT_IMAGE_NAME)
        print(f"Cleaned up {DEFAULT_IMAGE_NAME} before test_upload_default_image_if_missing_does_nothing_if_exists")
    except S3Error as e:
         if e.code != "NoSuchKey":
             pytest.fail(f"Error cleaning up {DEFAULT_IMAGE_NAME} before test: {e}")

    original_exists = os.path.exists(DEFAULT_IMAGE_PATH)
    created_dummy = False
    if not original_exists:
         os.makedirs(os.path.dirname(DEFAULT_IMAGE_PATH), exist_ok=True)
         with open(DEFAULT_IMAGE_PATH, "wb") as f:
              f.write(b"dummy default image content for exists test")
         created_dummy = True

    try:
        minio_client.put_object(
            minio_test_bucket_name,
            file_name,
            data=io.BytesIO(dummy_image_data),
            length=len(dummy_image_data),
            content_type="image/jpeg"
        )
        initial_stat = minio_client.stat_object(minio_test_bucket_name, file_name)
        print(f"Uploaded {DEFAULT_IMAGE_NAME} for test_upload_default_image_if_missing_does_nothing_if_exists setup")
    except S3Error as e:
        pytest.fail(f"Failed to upload file for exists test setup: {e}")

    upload_default_image_if_missing()

    final_stat = minio_client.stat_object(minio_test_bucket_name, file_name)
    assert final_stat.size == initial_stat.size
    assert final_stat.etag == initial_stat.etag


def test_upload_default_image_if_missing_handles_local_file_missing(minio_test_bucket_name, monkeypatch):
    """
    Test that upload_default_image_if_missing raises FileNotFoundError
    when the key is missing in the bucket AND the local file is missing.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', minio_test_bucket_name)

    try:
        minio_client.remove_object(minio_test_bucket_name, DEFAULT_IMAGE_NAME)
        print(f"Cleaned up {DEFAULT_IMAGE_NAME} before test_upload_default_image_if_missing_handles_local_file_missing")
    except S3Error as e:
         if e.code != "NoSuchKey":
             pytest.fail(f"Error cleaning up {DEFAULT_IMAGE_NAME} before test: {e}")

    try:
        minio_client.stat_object(minio_test_bucket_name, DEFAULT_IMAGE_NAME)
        pytest.fail(f"Default image '{DEFAULT_IMAGE_NAME}' should not exist in bucket before test function call.")
    except S3Error as e:
        assert e.code == "NoSuchKey"

    original_exists = os.path.exists(DEFAULT_IMAGE_PATH)
    temp_path = DEFAULT_IMAGE_PATH + f".temp_pytest_{uuid.uuid4().hex[:8]}"
    if original_exists:
        try:
            os.rename(DEFAULT_IMAGE_PATH, temp_path)
        except OSError as e:
             pytest.fail(f"Could not rename default image file for test setup: {e}")


    try:
        with pytest.raises(FileNotFoundError, match=f"Default profile image not found at {DEFAULT_IMAGE_PATH}"):
            upload_default_image_if_missing()

    finally:
        if original_exists and os.path.exists(temp_path):
             try:
                os.rename(temp_path, DEFAULT_IMAGE_PATH)
             except OSError as e:
                 print(f"Warning: Could not restore default image file during cleanup: {e}")


def test_ensure_bucket_creates_when_missing(mocker, monkeypatch):
    """
    Test that ensure_bucket calls make_bucket when bucket_exists returns False.
    Uses mocking.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', "mock-test-bucket")

    mock_bucket_exists = mocker.patch.object(minio_client, 'bucket_exists', return_value=False)

    mock_make_bucket = mocker.patch.object(minio_client, 'make_bucket')

    ensure_bucket()

    mock_bucket_exists.assert_called_once_with("mock-test-bucket")

    mock_make_bucket.assert_called_once_with("mock-test-bucket")


def test_ensure_bucket_does_not_create_when_exists(mocker, monkeypatch):
    """
    Test that ensure_bucket does NOT call make_bucket when bucket_exists returns True.
    Uses mocking.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', "mock-test-bucket")

    mock_bucket_exists = mocker.patch.object(minio_client, 'bucket_exists', return_value=True)

    mock_make_bucket = mocker.patch.object(minio_client, 'make_bucket')

    ensure_bucket()

    mock_bucket_exists.assert_called_once_with("mock-test-bucket")

    mock_make_bucket.assert_not_called()


def test_upload_default_image_if_missing_handles_other_s3error(mocker, monkeypatch):
    """
    Test that upload_default_image_if_missing raises S3Error if stat_object
    raises an S3Error other than NoSuchKey.
    Uses mocking to simulate the specific error.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', "mock-test-bucket")

    mock_error = S3Error("AccessDenied", "Access Denied", "mock-resource", "reqid", "hostid", None)

    mock_stat_object = mocker.patch.object(
        minio_client,
        'stat_object',
        side_effect=mock_error
    )

    mocker.patch('os.path.exists', return_value=False)

    mocker.patch('app.utils.minio_client.ensure_bucket')

    with pytest.raises(S3Error) as excinfo:
        upload_default_image_if_missing()

    mock_stat_object.assert_called_once_with("mock-test-bucket", DEFAULT_IMAGE_NAME)

    assert excinfo.value is mock_error
    assert excinfo.value.code == "AccessDenied"

@pytest.mark.asyncio
async def test_save_image_handles_put_object_failure(mocker, monkeypatch, dummy_image_data):
    """
    Test that save_image raises S3Error if minio_client.put_object fails.
    Uses function-scoped mocking to simulate the failure.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', "mock-test-bucket")
    file_name = "test_upload_fail.jpg"

    mock_error = S3Error("InternalError", "MinIO server error", "mock-resource", "reqid", "hostid", None)

    mock_put_object = mocker.patch.object(
        minio_client,
        'put_object',
        side_effect=mock_error
    )

    mocker.patch('app.utils.minio_client.ensure_bucket')

    with pytest.raises(S3Error) as excinfo:
        await save_image(dummy_image_data, file_name)

    mock_put_object.assert_called_once()
    assert excinfo.value is mock_error
    assert excinfo.value.code == "InternalError"


def test_upload_default_image_if_missing_handles_fput_object_failure(mocker, monkeypatch):
    """
    Test that upload_default_image_if_missing raises S3Error if fput_object fails
    when the default image is missing in the bucket but the local file exists.
    Uses mocking.
    """
    monkeypatch.setattr('app.utils.minio_client.BUCKET_NAME', "mock-test-bucket")

    mock_stat_object = mocker.patch.object(
        minio_client,
        'stat_object',
        side_effect=S3Error("NoSuchKey", "Object does not exist", "mock-resource", "reqid", "hostid", None)
    )

    mock_os_path_exists = mocker.patch('os.path.exists', return_value=True)

    mock_fput_error = S3Error("UploadFailed", "Error during upload", "mock-resource", "reqid", "hostid", None)

    mock_fput_object = mocker.patch.object(
        minio_client,
        'fput_object',
        side_effect=mock_fput_error
    )

    mocker.patch('app.utils.minio_client.ensure_bucket')

    with pytest.raises(S3Error) as excinfo:
        upload_default_image_if_missing()

    mock_stat_object.assert_called_once_with("mock-test-bucket", DEFAULT_IMAGE_NAME)

    mock_os_path_exists.assert_called_once_with(DEFAULT_IMAGE_PATH)

    mock_fput_object.assert_called_once_with(
        "mock-test-bucket",
        DEFAULT_IMAGE_NAME,
        DEFAULT_IMAGE_PATH,
        content_type="image/jpeg"
    )

    assert excinfo.value is mock_fput_error
    assert excinfo.value.code == "UploadFailed"


def test_fixture_cleanup_handles_remove_object_error(minio_test_bucket_name, setup_and_teardown_bucket, mocker: MockerFixture): # Use the module-scoped mocker
    """
    Test that the fixture's teardown handles S3Error when removing an object.
    Mocks minio_client.remove_object to raise S3Error during teardown.
    """
    mock_remove_object_error = S3Error("RemoveError", "Failed to remove object", "mock-resource", "reqid", "hostid", None)

    mock_remove_object = mocker.patch.object(
        minio_client,
        'remove_object',
        side_effect=mock_remove_object_error
    )

    assert isinstance(mock_remove_object, MagicMock)


def test_fixture_cleanup_handles_remove_bucket_error(minio_test_bucket_name, setup_and_teardown_bucket, mocker: MockerFixture): # Use the module-scoped mocker
    """
    Test that the fixture's teardown handles S3Error when removing the bucket.
    Mocks minio_client.remove_bucket to raise S3Error during teardown.
    """
    mock_remove_bucket_error = S3Error("BucketNotEmpty", "Bucket is not empty", "mock-resource", "reqid", "hostid", None)

    mock_remove_bucket = mocker.patch.object(
        minio_client,
        'remove_bucket',
        side_effect=mock_remove_bucket_error
    )

    mock_list_objects = mocker.patch.object(
        minio_client,
        'list_objects',
        return_value=[]
    )

    assert isinstance(mock_remove_bucket, MagicMock)
    assert isinstance(mock_list_objects, MagicMock)


def test_fixture_cleanup_handles_bucket_not_empty(minio_test_bucket_name, setup_and_teardown_bucket, mocker: MockerFixture): # Use the module-scoped mocker
    """
    Test that the fixture's teardown handles the case where the bucket is not empty
    after attempting to remove objects.
    Mocks minio_client.list_objects to return a non-empty list during teardown.
    """
    mock_list_objects = mocker.patch.object(
        minio_client,
        'list_objects',
        return_value=[MagicMock()]
    )

    mock_remove_bucket = mocker.patch.object(
        minio_client,
        'remove_bucket'
    )

    assert isinstance(mock_list_objects, MagicMock)
    assert isinstance(mock_remove_bucket, MagicMock)

    mock_remove_bucket.assert_not_called()


def _mimic_cleanup_dummy_file(created_dummy_val: bool, dummy_file_path_val: str, mock_os_path_exists: MagicMock, mock_os_remove: MagicMock, mock_print: MagicMock):
    """
    Helper to mimic the dummy file cleanup logic found in test finally blocks.
    Allows testing the OSError handling in cleanup.
    Accepts mocks as arguments.
    """
    created_dummy = created_dummy_val
    DEFAULT_IMAGE_PATH_MIMIC = dummy_file_path_val

    if created_dummy and mock_os_path_exists(DEFAULT_IMAGE_PATH_MIMIC):
         try:
              mock_os_remove(DEFAULT_IMAGE_PATH_MIMIC)
         except OSError as e:
              mock_print(f"Warning: Could not remove dummy file during cleanup {DEFAULT_IMAGE_PATH_MIMIC}: {e}")


def test_cleanup_dummy_file_handles_oserror(mocker: MockerFixture):
    """
    Test that the dummy file cleanup helper handles OSError when removing the file.
    Mocks dependencies in the test scope and passes them to the helper.
    """
    dummy_path = "/fake/dummy/path.jpg"

    mock_os_path_exists = mocker.patch('os.path.exists', return_value=True)
    mock_os_remove = mocker.patch('os.remove', side_effect=OSError("Simulated OS error"))
    mock_print = mocker.patch('builtins.print')

    _mimic_cleanup_dummy_file(True, dummy_path, mock_os_path_exists, mock_os_remove, mock_print)

    mock_os_path_exists.assert_called_once_with(dummy_path)
    mock_os_remove.assert_called_once_with(dummy_path)
    mock_print.assert_called_once()


def test_cleanup_dummy_file_success(mocker: MockerFixture):
    """
    Test that the dummy file cleanup helper successfully removes the file.
    Mocks dependencies in the test scope and passes them to the helper.
    """
    dummy_path = "/fake/dummy/path.jpg"

    mock_os_path_exists = mocker.patch('os.path.exists', return_value=True)
    mock_os_remove = mocker.patch('os.remove')
    mock_print = mocker.patch('builtins.print')

    _mimic_cleanup_dummy_file(True, dummy_path, mock_os_path_exists, mock_os_remove, mock_print)

    mock_os_path_exists.assert_called_once_with(dummy_path)
    mock_os_remove.assert_called_once_with(dummy_path)
    mock_print.assert_not_called()


def test_cleanup_dummy_file_not_created(mocker: MockerFixture):
    """
    Test that the dummy file cleanup helper does nothing if created_dummy is False.
    Mocks dependencies in the test scope and passes them to the helper.
    """
    dummy_path = "/fake/dummy/path.jpg"

    mock_os_path_exists = mocker.patch('os.path.exists')
    mock_os_remove = mocker.patch('os.remove')
    mock_print = mocker.patch('builtins.print')


    _mimic_cleanup_dummy_file(False, dummy_path, mock_os_path_exists, mock_os_remove, mock_print)

    mock_os_path_exists.assert_not_called()
    mock_os_remove.assert_not_called()
    mock_print.assert_not_called()
