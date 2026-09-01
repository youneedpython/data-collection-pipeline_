from unittest.mock import Mock

from src.data_collection_pipeline.s3_storage import upload_raw_html_batch


def test_upload_raw_html_batch(tmp_path):
    batch_dir = tmp_path / '20260830_153000'
    batch_dir.mkdir()

    first_file = batch_dir / 'books_page_001.html'
    second_file = batch_dir / 'books_page_002.html'

    first_file.write_text(
        '<html>page 1</html>',
        encoding='utf-8',
    )

    second_file.write_text(
        '<html>page 2</html>',
        encoding='utf-8',
    )

    mock_s3_client = Mock()

    object_keys = upload_raw_html_batch(
        raw_batch_dir=batch_dir,
        bucket_name='test-books-bucket',
        s3_client=mock_s3_client,
    )

    assert object_keys == [
        'raw/20260830_153000/books_page_001.html',
        'raw/20260830_153000/books_page_002.html',
    ]

    assert mock_s3_client.upload_file.call_count == 2