"""
데이터 수집 파이프라인에서 사용하는
Amazon S3 저장 기능을 제공하는 모듈입니다.
"""

from pathlib import Path
from typing import Any


def upload_raw_html_batch(
    raw_batch_dir: Path,
    bucket_name: str,
    s3_client: Any | None = None,
) -> list[str]:
    """
    Crawling 단계에서 생성한 HTML 파일을
    Amazon S3 raw 영역에 업로드합니다.

    Args:
        raw_batch_dir:
            Crawling 단계에서 생성된 로컬 임시 배치 폴더

        bucket_name:
            HTML 파일을 저장할 S3 Bucket 이름

        s3_client:
            테스트 등을 위해 외부에서 전달할 수 있는 S3 Client

    Returns:
        S3에 업로드된 Object Key 목록
    """

    if not bucket_name:
        raise ValueError('S3 Bucket 이름이 지정되지 않았습니다.')

    if not raw_batch_dir.exists():
        raise FileNotFoundError(
            f'Raw HTML 배치 폴더가 존재하지 않습니다: {raw_batch_dir}'
        )

    ## Lambda Runtime에는 boto3가 기본으로 제공됨
    if s3_client is None:
        import boto3

        s3_client = boto3.client('s3')

    batch_id = raw_batch_dir.name
    raw_prefix = f'raw/{batch_id}'

    html_files = sorted(raw_batch_dir.glob('*.html'))

    if not html_files:
        raise FileNotFoundError(
            f'업로드할 HTML 파일이 없습니다: {raw_batch_dir}'
        )

    object_keys: list[str] = []

    for html_file in html_files:
        object_key = f'{raw_prefix}/{html_file.name}'

        s3_client.upload_file(
            str(html_file),
            bucket_name,
            object_key,
        )

        object_keys.append(object_key)

        print(
            f'S3 업로드 완료 : '
            f's3://{bucket_name}/{object_key}'
        )

    return object_keys