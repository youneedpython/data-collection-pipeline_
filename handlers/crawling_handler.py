"""
정적 웹페이지 수집 작업을 실행하는 AWS Lambda Handler입니다.

Lambda event에서 수집 페이지 범위를 전달받아
기존 run_crawling()을 실행합니다.
"""

from src.data_collection_pipeline.config import END_PAGE, START_PAGE
from src.data_collection_pipeline.crawling import run_crawling


def lambda_handler(event: dict | None, context: object) -> dict[str, object]:
    """
    정적 웹페이지 Crawling Lambda의 실행 진입점입니다.

    Args:
        event:
            Lambda 호출 이벤트

            예:
                {
                    "start_page": 1,
                    "end_page": 3
                }

        context:
            AWS Lambda Runtime Context

    Returns:
        수집 작업 결과 정보
    """

    if event is None:
        event = {}

    start_page = int(event.get('start_page', START_PAGE))
    end_page = int(event.get('end_page', END_PAGE))

    raw_batch_dir = run_crawling(start_page=start_page, end_page=end_page)

    request_id = getattr(context, 'aws_request_id', None)

    return {
        'stage': 'crawling',
        'status': 'SUCCEEDED',
        'batch_id': raw_batch_dir.name,
        'start_page': start_page,
        'end_page': end_page,
        'temporary_batch_dir': str(raw_batch_dir),
        'request_id': request_id,
    }