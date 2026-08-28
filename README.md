# Data Collection Pipeline

정적 웹페이지에서 데이터를 수집하고  
**수집(Crawling) → 파싱(Extract) → 전처리(Preprocess) → MySQL 저장(Load)** 까지 수행하는 데이터 수집 파이프라인 프로젝트입니다.

현재 프로젝트는 [Books to Scrape](https://books.toscrape.com/) 사이트를 대상으로  
페이지네이션 기반 정적 웹 크롤링, 배치 단위 데이터 관리, 데이터 검증, MySQL UPSERT를 구현하고 있습니다.

또한 `pytest`, `Ruff`, GitHub Actions를 이용하여 코드 품질과 테스트를 자동으로 검증하는 CI 환경을 구성합니다.

---

## 1. 프로젝트 목표

이 프로젝트의 주요 목표는 다음과 같습니다.

- 정적 웹페이지의 페이지네이션 데이터를 수집합니다.
- 한 번의 수집 실행을 하나의 배치로 관리합니다.
- 원본 HTML, 파싱 CSV, 전처리 CSV를 단계별로 분리하여 저장합니다.
- 각 단계의 반환값을 다음 단계의 입력값으로 전달합니다.
- 데이터 저장 전 필수 컬럼, 결측값, 중복값, 자료형을 검증합니다.
- 전처리 완료 데이터를 MySQL `books` 테이블에 UPSERT합니다.
- 공통 설정과 데이터베이스 연결 책임을 별도 모듈로 분리합니다.
- `pytest`와 `Ruff`를 이용해 로컬에서 코드와 테스트를 검증합니다.
- GitHub Actions를 이용해 `push`, `pull_request` 시 CI를 자동 실행합니다.

---

## 2. 전체 파이프라인

현재 로컬 데이터 파이프라인은 다음 순서로 실행됩니다.

```text
Books to Scrape
       ↓
Crawling
       ↓
Raw HTML
       ↓
Extract
       ↓
Parsed CSV
       ↓
Preprocess
       ↓
Processed CSV
       ↓
Load
       ↓
MySQL
```

실행 함수 기준으로 보면 다음과 같습니다.

```text
run_crawling()
      ↓
run_extract()
      ↓
run_preprocess()
      ↓
run_load()
```

`main.py`가 각 실행 함수를 순서대로 연결하는 프로젝트 진입점 역할을 합니다.

---

## 3. 프로젝트 구조

현재 프로젝트의 주요 구조는 다음과 같습니다.

```text
data-collection-pipeline/
│
├─ .github/
│  └─ workflows/
│     └─ ci.yml
│
├─ data/
│  ├─ raw/
│  │  └─ html/
│  │     └─ YYYYMMDD_HHMMSS/
│  │        ├─ books_page_001.html
│  │        ├─ books_page_002.html
│  │        └─ ...
│  │
│  ├─ interim/
│  │  └─ YYYYMMDD_HHMMSS/
│  │     ├─ books_page_001_parsed.csv
│  │     ├─ books_page_002_parsed.csv
│  │     └─ ...
│  │
│  └─ processed/
│     └─ books_pages_001_003_processed_YYYYMMDD_HHMMSS.csv
│
├─ docs/
│  ├─ 00_static_pipeline_docs/
│  ├─ 01_requirements/
│  │  ├─ 데이터_수집_파이프라인_요구사항_정의서_v1.0.docx
│  │  ├─ 데이터_수집_파이프라인_요구사항_정의서_v1_1.docx
│  │  └─ 데이터_수집_파이프라인_요구사항_정의서_v2.0.docx
│  │
│  └─ 02_architecture/
│     ├─ 빅데이터_플랫폼_아키텍처_설계서_v1.0.docx
│     └─ 빅데이터_플랫폼_아키텍처_설계서_v2.0.docx
│
├─ notebooks/
│
├─ src/
│  └─ data_collection_pipeline/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ database.py
│     ├─ crawling.py
│     ├─ extract.py
│     ├─ preprocess.py
│     └─ load.py
│
├─ tests/
│  ├─ test_extract.py
│  └─ test_preprocess.py
│
├─ .env
├─ .env.example
├─ .gitignore
├─ main.py
├─ pyproject.toml
├─ README.md
├─ requirements.txt
└─ requirements-dev.txt
```

`data/`, `.env`, `notebooks/` 등은 로컬 실행 또는 학습 과정에서 사용하는 파일입니다.  
Git 추적 여부는 `.gitignore` 설정을 기준으로 관리합니다.

---

## 4. 주요 모듈

### 4.1 `main.py`

전체 데이터 수집 파이프라인을 실행하는 진입점입니다.

```python
raw_batch_dir = run_crawling()

parsed_csv_files = run_extract(raw_batch_dir)

interim_batch_dir = parsed_csv_files[0].parent

processed_csv_file = run_preprocess(interim_batch_dir)

load_summary = run_load(processed_csv_file)
```

각 단계에서 생성된 결과를 다음 단계의 입력값으로 전달합니다.

| 함수 | 입력 | 반환값 |
|---|---|---|
| `run_crawling()` | 기본 수집 설정 | raw HTML 배치 폴더 `Path` |
| `run_extract()` | raw HTML 배치 폴더 `Path` | parsed CSV 경로 `list[Path]` |
| `run_preprocess()` | interim 배치 폴더 `Path` | processed CSV `Path` |
| `run_load()` | processed CSV `Path` | MySQL 저장 결과 `dict` |

---

### 4.2 `config.py`

프로젝트에서 공통으로 사용하는 설정을 관리합니다.

주요 설정:

```text
PROJECT_DIR
DATA_DIR
RAW_HTML_DIR
INTERIM_DIR
PROCESSED_DIR
ENV_FILE

BASE_URL
SOURCE_SITE

START_PAGE
END_PAGE

CONNECT_TIMEOUT
READ_TIMEOUT
REQUEST_INTERVAL
HEADERS

APP_TIMEZONE
```

현재 `APP_TIMEZONE`은 다음과 같이 정의되어 있습니다.

```text
Asia/Seoul
```

각 단계 모듈은 필요한 설정만 `config.py`에서 import하여 사용합니다.

---

### 4.3 `database.py`

MySQL 연결 설정과 SQLAlchemy Engine 생성을 담당합니다.

주요 함수:

```text
load_database_config()
create_mysql_engine()
test_mysql_connection()
```

DB 연결 정보는 로컬 `.env`에서 읽습니다.

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

데이터 적재 로직과 데이터베이스 연결 책임을 분리하여 관리합니다.

---

### 4.4 `crawling.py`

Books to Scrape 페이지를 순회하면서 HTTP 요청을 보내고  
응답받은 원본 HTML을 배치 단위로 저장합니다.

주요 함수:

```text
fetch_html()
ensure_directory()
create_batch_directory()
save_raw_html()
run_crawling()
```

출력 예:

```text
data/raw/html/20260826_172800/
├─ books_page_001.html
├─ books_page_002.html
└─ books_page_003.html
```

---

### 4.5 `extract.py`

raw 배치 폴더의 HTML 파일을 읽고 필요한 도서 데이터를 파싱하여  
페이지별 interim CSV를 생성합니다.

주요 함수:

```text
parse_batch_directory_name()
find_latest_batch_directory()
parse_raw_file_name()
find_raw_html_files()
load_raw_html()
get_required_tag()
parse_rating()
parse_book_item()
parse_books()
validate_books_dataframe()
create_interim_batch_directory()
save_parsed_csv()
verify_saved_csv()
run_extract()
```

출력 예:

```text
data/interim/20260826_172800/
├─ books_page_001_parsed.csv
├─ books_page_002_parsed.csv
└─ books_page_003_parsed.csv
```

---

### 4.6 `preprocess.py`

페이지별 parsed CSV를 하나의 DataFrame으로 통합하고  
전처리와 데이터 검증을 수행합니다.

주요 처리:

```text
페이지별 CSV 탐색
→ 페이지 순서 검증
→ CSV 통합
→ 문자열 정리
→ 가격 변환
→ 재고 상태 변환
→ 자료형 변환
→ book_id 생성
→ 메타데이터 추가
→ 중복 제거
→ 데이터 검증
→ processed CSV 저장
```

주요 함수:

```text
parse_batch_directory_name()
find_latest_interim_batch_directory()
parse_parsed_file_name()
find_parsed_csv_files()
load_parsed_csv()
validate_input_books()
load_parsed_csv_files()
clean_string_columns()
parse_price()
parse_availability()
preprocess_books()
validate_processed_books()
ensure_directory()
save_csv_atomically()
build_processed_file_path()
save_processed_csv()
verify_saved_csv()
run_preprocess()
```

출력 예:

```text
data/processed/
└─ books_pages_001_003_processed_20260826_172800.csv
```

---

### 4.7 `load.py`

processed CSV를 읽고 배치 정보와 데이터 상태를 검증한 뒤  
MySQL `books` 테이블에 저장합니다.

주요 처리:

```text
processed CSV 입력
→ 파일명 및 배치 정보 검증
→ DB 저장용 자료형 변환
→ database.py를 통한 MySQL Engine 생성
→ books 테이블 생성
→ UPSERT
```

주요 함수:

```text
parse_processed_file_name()
find_latest_processed_csv()
load_processed_csv()
validate_processed_batch()
prepare_and_validate_dataframe()
dataframe_to_database_records()
create_books_table()
upsert_books()
run_load()
```

동일한 데이터가 다시 수집된 경우 INSERT 또는 UPDATE가 수행되도록 UPSERT 방식으로 저장합니다.

---

### 4.8 `__init__.py`

파이프라인의 주요 실행 함수를 패키지 외부에 제공합니다.

```python
from .crawling import run_crawling
from .extract import run_extract
from .load import run_load
from .preprocess import run_preprocess
```

`main.py`는 각 모듈의 세부 구현보다 주요 실행 함수만 import하여 사용합니다.

---

## 5. 배치 관리

한 번의 수집 실행은 하나의 배치로 관리합니다.

배치 이름 형식:

```text
YYYYMMDD_HHMMSS
```

예:

```text
20260826_172800
```

raw와 interim은 동일한 배치 이름을 사용합니다.

```text
data/raw/html/20260826_172800/
data/interim/20260826_172800/
```

processed 데이터는 파일명에 페이지 범위와 배치 시각을 포함합니다.

```text
books_pages_001_003_processed_20260826_172800.csv
            ───────             ───────────────
           페이지 범위              배치 시각
```

이를 통해 한 번의 수집 작업이 raw → interim → processed → MySQL로 처리되는 과정을 추적할 수 있습니다.

---

## 6. 단계별 데이터 상태

| 단계 | 저장 위치 | 데이터 상태 |
|---|---|---|
| Crawling | `data/raw/html/<batch>/` | 서버 응답 원본 HTML |
| Extract | `data/interim/<batch>/` | 페이지별 파싱 CSV |
| Preprocess | `data/processed/` | 통합·전처리·검증 완료 CSV |
| Load | MySQL `books` | DB 저장 완료 데이터 |

---

## 7. 환경 설정

### 7.1 실행 패키지 설치

프로젝트 실행에 필요한 패키지를 설치합니다.

```bash
python -m pip install -r requirements.txt
```

현재 주요 실행 의존성:

```text
requests
pandas
beautifulsoup4
python-dotenv
SQLAlchemy
PyMySQL
```

---

### 7.2 개발 및 CI 패키지 설치

테스트와 코드 품질 검사를 포함한 개발 환경은 다음 명령으로 구성합니다.

```bash
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt`:

```text
-r requirements.txt

pytest
ruff
```

따라서 실행 패키지와 함께 `pytest`, `Ruff`가 설치됩니다.

---

### 7.3 `.env` 설정

프로젝트 루트의 `.env.example`을 참고하여 `.env`를 작성합니다.

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

`.env`에는 DB 비밀번호 등의 민감정보가 포함되므로 Git에 커밋하지 않습니다.

---

## 8. 파이프라인 실행

프로젝트 루트에서 다음 명령으로 전체 파이프라인을 실행합니다.

```bash
python main.py
```

실행 흐름:

```text
main.py
  │
  ├─ run_crawling()
  │      ↓
  │   raw_batch_dir
  │
  ├─ run_extract(raw_batch_dir)
  │      ↓
  │   parsed_csv_files
  │
  ├─ run_preprocess(interim_batch_dir)
  │      ↓
  │   processed_csv_file
  │
  └─ run_load(processed_csv_file)
         ↓
      load_summary
```

---

## 9. 테스트

테스트 코드는 `tests/`에 위치합니다.

```text
tests/
├─ test_extract.py
└─ test_preprocess.py
```

현재 테스트 대상은 외부 네트워크나 MySQL에 직접 의존하지 않는 함수 중심으로 구성합니다.

주요 테스트 대상:

```text
parse_batch_directory_name()
parse_raw_file_name()
parse_parsed_file_name()
parse_price()
parse_availability()
build_processed_file_path()
```

전체 테스트 실행:

```bash
python -m pytest -v
```

`pyproject.toml`에서 pytest 테스트 경로를 지정합니다.

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

---

## 10. Ruff 코드 품질 검사

Ruff를 이용하여 Python 코드의 기본 오류와 코드 스타일을 검사합니다.

실행:

```bash
python -m ruff check .
```

현재 `pyproject.toml`에서 다음 규칙을 적용합니다.

```text
E4
E7
E9
F
I
DTZ
RUF
```

주요 검사 항목:

```text
Python 기본 문법 및 스타일
미사용 또는 잘못된 코드
import 정렬
datetime timezone 사용
Ruff 권장 코드 품질 규칙
```

Python 기준 버전:

```text
Python 3.13
```

한 줄 길이 기준:

```text
100
```

---

## 11. GitHub Actions CI

CI workflow는 다음 위치에 있습니다.

```text
.github/workflows/ci.yml
```

CI 실행 조건:

```text
main branch push
또는
main branch 대상 pull_request
```

실행 흐름:

```text
GitHub Push / Pull Request
        ↓
Checkout Repository
        ↓
Python 3.13 설정
        ↓
requirements-dev.txt 설치
        ↓
Ruff 검사
        ↓
pytest 실행
        ↓
CI 성공 / 실패
```

CI에서는 다음 두 명령을 자동으로 수행합니다.

```bash
python -m ruff check .
python -m pytest -v
```

따라서 로컬과 GitHub Actions에서 동일한 검사 명령을 사용할 수 있습니다.

---

## 12. 프로젝트 문서

프로젝트 관련 문서는 `docs/`에 목적별로 분리하여 보관합니다.

```text
docs/
├─ 00_static_pipeline_docs/
│  ├─ README.md
│  ├─ 06_1_crawling.md
│  ├─ 06_2_parsing.md
│  ├─ 06_3_preprocessing.md
│  └─ 06_4_mysql_load.md
│
├─ 01_requirements/
│  └─ 데이터 수집 파이프라인 요구사항 정의서
│
└─ 02_architecture/
   └─ 빅데이터 플랫폼 아키텍처 설계서
```

각 폴더의 역할:

| 디렉터리 | 역할 |
|---|---|
| `00_static_pipeline_docs/` | 정적 데이터 수집 파이프라인 단계별 설명 |
| `01_requirements/` | 데이터 수집 파이프라인 요구사항 정의서 |
| `02_architecture/` | 빅데이터 플랫폼 아키텍처 설계서 |

---

## 13. Git 관리 정책

이 프로젝트는 블랙리스트 방식의 `.gitignore`를 사용합니다.

프로젝트 파일은 기본적으로 Git에서 추적하고,  
로컬 환경·비밀정보·실행 산출물·캐시 등을 제외합니다.

주요 제외 대상:

```text
.env
data/
logs/
*.log
docs/
notebooks/

__pycache__/
.pytest_cache/
.ruff_cache/

.venv/
venv/

.ipynb_checkpoints/
.vscode/
.idea/

build/
dist/
.aws-sam/
```

`.env.example`은 실제 비밀번호가 포함되지 않은 환경설정 예제이므로 Git에서 추적합니다.

현재 `.gitignore`에 `docs/`가 포함되어 있으므로 `docs/` 아래 문서는 로컬에서 관리됩니다.  
문서도 GitHub에서 버전 관리하려면 `.gitignore`의 `docs/` 제외 규칙을 제거해야 합니다.

---

## 14. 프로젝트 설계 원칙

이 프로젝트는 다음 원칙을 기준으로 구성합니다.

- 원본 데이터는 수정하지 않고 `raw`에 보관합니다.
- 한 번의 수집 실행을 하나의 배치로 관리합니다.
- `raw`와 `interim`은 동일한 배치 이름을 사용합니다.
- 페이지별 원본 HTML과 parsed CSV를 유지합니다.
- 페이지별 parsed CSV는 전처리 단계에서 하나의 DataFrame으로 통합합니다.
- 전처리와 검증이 완료된 데이터만 `processed`에 저장합니다.
- 데이터 저장 전 필수 컬럼, 결측값, 중복값과 자료형을 검증합니다.
- 데이터베이스 비밀번호와 같은 민감정보는 `.env`로 분리합니다.
- 공통 설정은 `config.py`에서 관리합니다.
- 데이터베이스 연결 책임은 `database.py`에서 관리합니다.
- `main.py`는 파이프라인 실행 함수 연결에 집중합니다.
- 각 단계의 반환값을 다음 단계의 입력값으로 전달합니다.
- 테스트와 코드 품질 검사를 로컬과 CI에서 동일한 명령으로 수행합니다.

---

## 15. ETL 관점의 데이터 처리

현재 프로젝트를 ETL 관점에서 보면 다음과 같이 구분할 수 있습니다.

```text
Extract
├─ 웹페이지 요청
├─ 원본 HTML 저장
└─ HTML 파싱

Transform
├─ 페이지별 CSV 통합
├─ 문자열 정리
├─ 자료형 변환
├─ 가격 변환
├─ 재고 상태 변환
├─ 중복 처리
├─ 메타데이터 생성
└─ 데이터 검증

Load
├─ processed CSV 읽기
├─ 배치 정보 검증
├─ MySQL 연결
├─ books 테이블 생성
└─ INSERT / UPDATE
```

전체 ETL 흐름:

```text
Extract → Transform → Load
```

---

## 16. 현재 구성 및 확장 방향

현재 프로젝트는 다음 구성까지 포함합니다.

```text
정적 웹 크롤링
→ 페이지네이션 수집
→ raw / interim / processed 데이터 계층
→ MySQL 저장
→ Python 모듈 분리
→ 공통 설정 분리
→ DB 연결 모듈 분리
→ pytest 단위 테스트
→ Ruff 코드 품질 검사
→ GitHub Actions CI
```

이후에는 현재 로컬 파이프라인을 AWS 환경으로 확장하여  
배포 및 데이터 수집 자동화 구조를 구성할 수 있습니다.

```text
현재
Python Pipeline
+ pytest
+ Ruff
+ GitHub Actions CI

        ↓

향후
AWS 배포
+ 자동 데이터 수집
+ CI/CD
```
