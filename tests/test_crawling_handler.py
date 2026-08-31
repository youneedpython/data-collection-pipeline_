from pathlib import Path
from unittest.mock import Mock

from handlers import crawling_handler


def test_lambda_handler_runs_crawling(monkeypatch):
    batch_dir = Path('/tmp/data/raw/html/20260827_083000')

    mock_run_crawling = Mock(return_value=batch_dir)

    monkeypatch.setattr(crawling_handler, 'run_crawling', mock_run_crawling)

    context = Mock()
    context.aws_request_id = 'test-request-id'

    event = {'start_page': 1, 'end_page': 3}

    result = crawling_handler.lambda_handler(event, context)

    mock_run_crawling.assert_called_once_with(start_page=1, end_page=3)

    assert result == {
        'stage': 'crawling',
        'status': 'SUCCEEDED',
        'batch_id': '20260827_083000',
        'start_page': 1,
        'end_page': 3,
        'temporary_batch_dir': str(batch_dir),
        'request_id': 'test-request-id',
    }


def test_lambda_handler_uses_default_page_range(monkeypatch):
    batch_dir = Path('/tmp/data/raw/html/20260827_083000')

    mock_run_crawling = Mock(return_value=batch_dir)

    monkeypatch.setattr(crawling_handler, 'run_crawling', mock_run_crawling)

    result = crawling_handler.lambda_handler({}, None)

    mock_run_crawling.assert_called_once_with(start_page=1, end_page=3)

    assert result['batch_id'] == '20260827_083000'
    assert result['request_id'] is None