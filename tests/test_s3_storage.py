## AWS S3 API 호출을 가짜(Mock) 객체로 격리하기 위한 Mock 모듈 로드
from unittest.mock import Mock

## S3 스토리지 연동 함수들 로드 (Raw HTML 업로드, Interim CSV 다운로드, Processed CSV 업로드)
from src.data_collection_pipeline.s3_storage import (
    download_interim_batch,
    upload_processed_file,
    upload_raw_html_batch,
)


def test_upload_raw_html_batch(tmp_path):
    """
    로컬 배치 디렉터리의 Raw HTML 파일들이 S3 Raw 경로(raw/{batch_id}/)로
    누락 없이 정확하게 업로드되는지 검증합니다.
    """
    ## 테스트용 Raw HTML 배치 디렉터리 생성
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

    ## 실제 AWS S3 대신 Mock 객체 사용
    mock_s3_client = Mock()

    object_keys = upload_raw_html_batch(
        raw_batch_dir=batch_dir,
        bucket_name='test-books-bucket',
        s3_client=mock_s3_client,
    )

    ## 생성된 S3 Object Key 확인
    assert object_keys == [
        'raw/20260830_153000/books_page_001.html',
        'raw/20260830_153000/books_page_002.html',
    ]

    ## HTML 파일 2개가 각각 S3에 업로드되었는지 확인
    assert mock_s3_client.upload_file.call_count == 2


def test_download_interim_batch(tmp_path):
    """
    S3 Interim 영역의 CSV 파일 목록을 조회하고, 각 파일을 로컬 대상 디렉터리로
    올바른 경로와 파일명으로 다운로드하는지 검증합니다.
    """
    ## 테스트용 배치 정보
    batch_id = '20260901_035140'
    bucket_name = 'test-books-bucket'
    interim_prefix = f'interim/{batch_id}/'

    ## 실제 AWS S3 대신 Mock 객체 사용
    mock_s3_client = Mock()

    ## S3 list_objects_v2()가 반환할 가짜 객체 목록 설정
    mock_s3_client.list_objects_v2.return_value = {
        'Contents': [
            {
                'Key': (
                    f'{interim_prefix}'
                    'books_page_001_parsed.csv'
                )
            },
            {
                'Key': (
                    f'{interim_prefix}'
                    'books_page_002_parsed.csv'
                )
            },
            {
                'Key': (
                    f'{interim_prefix}'
                    'books_page_003_parsed.csv'
                )
            },
        ]
    }

    ## S3 Interim CSV 다운로드 함수 실행
    interim_batch_dir = download_interim_batch(
        bucket_name=bucket_name,
        batch_id=batch_id,
        interim_prefix=interim_prefix,
        destination_dir=tmp_path,
        s3_client=mock_s3_client,
    )

    ## 반환된 로컬 배치 디렉터리 확인
    assert interim_batch_dir == tmp_path / batch_id

    ## S3 객체 목록 조회가 올바른 인자로 호출되었는지 확인
    mock_s3_client.list_objects_v2.assert_called_once_with(
        Bucket=bucket_name,
        Prefix=interim_prefix,
    )

    ## CSV 파일 3개를 각각 다운로드했는지 확인
    assert mock_s3_client.download_file.call_count == 3

    ## 첫 번째 CSV 다운로드 호출 확인
    mock_s3_client.download_file.assert_any_call(
        bucket_name,
        (
            f'{interim_prefix}'
            'books_page_001_parsed.csv'
        ),
        str(
            tmp_path
            / batch_id
            / 'books_page_001_parsed.csv'
        ),
    )

    ## 두 번째 CSV 다운로드 호출 확인
    mock_s3_client.download_file.assert_any_call(
        bucket_name,
        (
            f'{interim_prefix}'
            'books_page_002_parsed.csv'
        ),
        str(
            tmp_path
            / batch_id
            / 'books_page_002_parsed.csv'
        ),
    )

    ## 세 번째 CSV 다운로드 호출 확인
    mock_s3_client.download_file.assert_any_call(
        bucket_name,
        (
            f'{interim_prefix}'
            'books_page_003_parsed.csv'
        ),
        str(
            tmp_path
            / batch_id
            / 'books_page_003_parsed.csv'
        ),
    )


def test_upload_processed_file(tmp_path):
    """
    최종 정제된 Processed CSV 파일이 S3 Processed 경로(processed/{batch_id}/)로
    단 1회 정확하게 업로드되는지 검증합니다.
    """
    ## 테스트용 배치 정보
    batch_id = '20260901_035140'
    bucket_name = 'test-books-bucket'

    ## 테스트용 Processed CSV 생성
    processed_file = (
        tmp_path
        / (
            'books_pages_001_003_processed_'
            f'{batch_id}.csv'
        )
    )

    processed_file.write_text(
        'book_id,title\n1,Test Book\n',
        encoding='utf-8',
    )

    ## 실제 AWS S3 대신 Mock 객체 사용
    mock_s3_client = Mock()

    ## Processed CSV 업로드 함수 실행
    object_key = upload_processed_file(
        processed_file=processed_file,
        bucket_name=bucket_name,
        batch_id=batch_id,
        s3_client=mock_s3_client,
    )

    expected_object_key = (
        f'processed/{batch_id}/'
        f'books_pages_001_003_processed_{batch_id}.csv'
    )

    ## 생성된 S3 Object Key 확인
    assert object_key == expected_object_key

    ## 올바른 Bucket과 Object Key로 업로드했는지 확인
    mock_s3_client.upload_file.assert_called_once_with(
        str(processed_file),
        bucket_name,
        expected_object_key,
    )