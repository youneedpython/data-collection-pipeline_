# Data Collection Pipeline

정적 웹페이지에서 데이터를 수집하고  
**수집 → 파싱 → 전처리 → MySQL 저장**까지 수행하는 데이터 수집 파이프라인 프로젝트입니다.

현재 실습에서는 [Books to Scrape](https://books.toscrape.com/) 사이트를 대상으로  
페이지네이션 기반 정적 웹 크롤링과 데이터 처리 과정을 단계별로 구현합니다.


## 1. 프로젝트 구조

```text
01-data-collection-pipeline/
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
│  └─ 06_static_pipeline/
│     ├─ README.md
│     ├─ 06_1_crawling.md
│     ├─ 06_2_parsing.md
│     ├─ 06_3_preprocessing.md
│     └─ 06_4_mysql_load.md
│
├─ notebooks/
│  └─ 01_static/
│
├─ src/
│  └─ data_collection_pipeline/
│     ├─ __init__.py
│     ├─ crawling.py
│     ├─ extract.py
│     ├─ preprocess.py
│     └─ load.py
│
├─ .env
├─ main.py
└─ README.md
```


## 2. 디렉터리 및 파일 설명

### `data/`

데이터 수집과 처리 과정에서 생성되는 파일을 저장합니다.


#### `data/raw/`

웹사이트에서 수집한 **원본 HTML 데이터**를 저장합니다.

```text
data/raw/html/YYYYMMDD_HHMMSS/
```

`YYYYMMDD_HHMMSS`는 한 번의 수집 실행을 구분하는 **배치(batch) 이름**입니다.

예:

```text
data/raw/html/20260810_081501/
├─ books_page_001.html
├─ books_page_002.html
└─ books_page_003.html
```

같은 크롤링 실행에서 수집한 HTML 파일은 동일한 배치 폴더에 저장합니다.

배치 시각은 디렉터리 이름에서 관리하므로  
페이지별 HTML 파일명에는 timestamp를 반복해서 저장하지 않습니다.


#### `data/interim/`

원본 HTML을 파싱한 **중간 데이터**를 저장합니다.

`raw`와 동일한 배치 이름을 사용하여  
수집 데이터와 파싱 결과를 연결합니다.

```text
data/interim/YYYYMMDD_HHMMSS/
```

예:

```text
data/interim/20260810_081501/
├─ books_page_001_parsed.csv
├─ books_page_002_parsed.csv
└─ books_page_003_parsed.csv
```

페이지별 파싱 결과를 개별 CSV로 유지하므로  
특정 페이지의 파싱 결과를 쉽게 확인하고 다시 처리할 수 있습니다.


#### `data/processed/`

페이지별 파싱 CSV를 하나의 DataFrame으로 통합하고  
전처리와 데이터 검증을 완료한 최종 CSV를 저장합니다.

예:

```text
data/processed/
└─ books_pages_001_003_processed_20260810_081501.csv
```

파일명에는 페이지 범위와 배치 시각이 포함됩니다.

```text
books_pages_001_003_processed_20260810_081501.csv
            ───────             ───────────────
           페이지 범위              배치 시각
```


### `docs/`

프로젝트 구조와 단계별 함수 설명 문서를 저장합니다.

현재 정적 페이지네이션 파이프라인 문서는 다음 위치에서 관리합니다.

```text
docs/
└─ 06_static_pipeline/
   ├─ README.md
   ├─ 06_1_crawling.md
   ├─ 06_2_parsing.md
   ├─ 06_3_preprocessing.md
   └─ 06_4_mysql_load.md
```

각 문서는 `06_1 ~ 06_4` 단계의 함수와 처리 흐름을 설명합니다.


### `notebooks/`

데이터 수집 파이프라인을 단계별로 학습하고 실습하기 위한  
Jupyter Notebook 파일을 저장합니다.

현재 정적 웹 크롤링 실습은 다음 위치에서 관리합니다.

```text
notebooks/
└─ 01_static/
```

주요 학습 흐름:

```text
06_1  페이지네이션 HTML 수집 및 함수 리팩토링
  ↓
06_2  페이지별 HTML 파싱
  ↓
06_3  페이지별 CSV 통합 및 전처리
  ↓
06_4  MySQL 저장
```


### `src/`

Notebook에서 학습하고 리팩토링한 코드를  
재사용 가능한 Python 모듈로 저장합니다.

현재 구조:

```text
src/
└─ data_collection_pipeline/
   ├─ __init__.py
   ├─ crawling.py
   ├─ extract.py
   ├─ preprocess.py
   └─ load.py
```

각 모듈의 역할은 다음과 같습니다.

| 모듈 | 역할 |
|---|---|
| `crawling.py` | 페이지네이션 방식으로 웹페이지를 요청하고 raw HTML 배치를 생성 |
| `extract.py` | raw HTML 배치를 파싱하여 페이지별 interim CSV 생성 |
| `preprocess.py` | interim CSV를 통합·전처리하여 processed CSV 생성 |
| `load.py` | processed CSV를 검증하고 MySQL `books` 테이블에 저장 |
| `__init__.py` | 파이프라인의 주요 실행 함수를 패키지 외부에 제공 |


### `.env`

MySQL 연결 정보와 같이 코드에 직접 작성하면 안 되는 환경 변수를 저장합니다.

예:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=data_collection
DB_USER=root
DB_PASSWORD="MySQL 비밀번호"
```

> `.env`에는 비밀번호와 같은 민감한 정보가 포함될 수 있으므로 Git 저장소에 커밋하지 않습니다.


### `main.py`

전체 데이터 수집 파이프라인을 실행하는 프로젝트의 진입점입니다.

현재 파이프라인은 **개별 파일이 아니라 배치 단위**로 데이터를 연결합니다.

```python
raw_batch_dir = run_crawling()

parsed_csv_files = run_extract(raw_batch_dir)

interim_batch_dir = parsed_csv_files[0].parent

processed_csv_file = run_preprocess(interim_batch_dir)

load_summary = run_load(processed_csv_file)
```

각 단계의 입력과 반환값은 다음과 같습니다.

| 함수 | 입력 | 반환값 |
|---|---|---|
| `run_crawling()` | 기본 설정 또는 페이지 범위 | raw HTML 배치 폴더 `Path` |
| `run_extract()` | raw HTML 배치 폴더 `Path` | 페이지별 parsed CSV `list[Path]` |
| `run_preprocess()` | interim 배치 폴더 `Path` | processed CSV `Path` |
| `run_load()` | processed CSV `Path` | MySQL 저장 결과 `dict` |

`run_extract()`가 반환한 페이지별 CSV는 모두 같은 interim 배치 폴더에 있으므로  
첫 번째 CSV의 부모 경로를 이용해 전처리 대상 배치를 구합니다.

```python
interim_batch_dir = parsed_csv_files[0].parent
```


### `README.md`

프로젝트의 목적, 디렉터리 구조, 데이터 흐름과 실행 구조를 설명합니다.

프로젝트 루트에 위치하며  
프로젝트를 처음 확인하는 사람이 전체 구조를 파악할 수 있도록 합니다.


## 3. 데이터 처리 흐름

한 번의 데이터 수집 작업은 동일한 배치 이름을 기준으로 연결됩니다.

```text
Books to Scrape
       ↓
run_crawling()
       ↓
data/raw/html/20260810_081501/
├─ books_page_001.html
├─ books_page_002.html
└─ books_page_003.html
       ↓
run_extract()
       ↓
data/interim/20260810_081501/
├─ books_page_001_parsed.csv
├─ books_page_002_parsed.csv
└─ books_page_003_parsed.csv
       ↓
run_preprocess()
       ↓
data/processed/
└─ books_pages_001_003_processed_20260810_081501.csv
       ↓
run_load()
       ↓
MySQL books
```

`raw`와 `interim`은 동일한 배치 디렉터리 이름을 사용하고,  
`processed`는 파일명에 동일한 배치 시각을 포함하여 데이터의 처리 흐름을 추적합니다.


## 4. 단계별 실행 함수

### 4.1 `run_crawling()`

페이지 범위를 순회하면서 웹페이지를 요청하고  
한 번의 수집 작업에 해당하는 raw HTML 배치 폴더를 생성합니다.

내부 주요 함수:

```text
fetch_html()
ensure_directory()
create_batch_directory()
save_raw_html()
```

처리 결과:

```text
data/raw/html/YYYYMMDD_HHMMSS/
```

반환값:

```text
raw HTML 배치 폴더 Path
```


### 4.2 `run_extract()`

`run_crawling()`이 반환한 raw 배치 폴더를 입력으로 받습니다.

배치 폴더의 HTML 파일을 페이지 순서대로 읽고 파싱한 뒤  
raw와 동일한 이름의 interim 배치 폴더에 CSV를 저장합니다.

입력:

```text
data/raw/html/YYYYMMDD_HHMMSS/
```

출력:

```text
data/interim/YYYYMMDD_HHMMSS/
├─ books_page_001_parsed.csv
├─ books_page_002_parsed.csv
└─ ...
```

반환값:

```text
list[Path]
```


### 4.3 `run_preprocess()`

interim 배치 폴더를 입력으로 받아 페이지별 CSV를 통합합니다.

주요 처리:

```text
CSV 통합
→ 문자열 정리
→ 가격 변환
→ 재고 상태 변환
→ 평점 자료형 변환
→ book_id 생성
→ 메타데이터 추가
→ 중복 제거
→ 데이터 검증
→ processed CSV 저장
```

반환값:

```text
processed CSV Path
```


### 4.4 `run_load()`

processed CSV를 읽고 파일명과 내부 배치 정보를 검증한 뒤  
MySQL `books` 테이블에 UPSERT합니다.

주요 처리:

```text
processed CSV 탐색 또는 입력
→ 배치 정보 검증
→ DB 저장용 자료형 변환
→ .env에서 DB 설정 로딩
→ SQLAlchemy Engine 생성
→ books 테이블 생성
→ UPSERT
```

반환값:

```text
dict[str, int | str]
```


## 5. 배치 디렉터리 관리

배치 이름은 데이터 수집 시작 시각을 다음 형식으로 저장합니다.

```text
YYYYMMDD_HHMMSS
```

예:

```text
20260810_081501
```

의미:

```text
2026년 08월 10일 08시 15분 01초
```

여러 번 크롤링을 실행해도 각 실행 결과가 별도의 배치로 관리됩니다.

```text
data/raw/html/
├─ 20260810_081501/
├─ 20260810_082015/
└─ 20260810_083122/
```

`interim`도 동일한 배치 이름을 사용합니다.

```text
data/interim/
├─ 20260810_081501/
├─ 20260810_082015/
└─ 20260810_083122/
```


## 6. 단계별 데이터 상태

| 단계 | 저장 위치 | 데이터 상태 |
|---|---|---|
| Crawling | `data/raw/html/<batch>/` | 서버에서 받은 원본 HTML |
| Parsing | `data/interim/<batch>/` | HTML에서 필요한 값을 추출한 페이지별 CSV |
| Preprocessing | `data/processed/` | 통합·자료형 변환·중복 처리·검증 완료 데이터 |
| Load | MySQL `books` | DB 저장이 완료된 도서 데이터 |


## 7. 페이지네이션 처리 예

3페이지를 수집한 경우:

```text
data/raw/html/20260810_081501/
├─ books_page_001.html
├─ books_page_002.html
└─ books_page_003.html
```

파싱 후:

```text
data/interim/20260810_081501/
├─ books_page_001_parsed.csv
├─ books_page_002_parsed.csv
└─ books_page_003_parsed.csv
```

전처리 후:

```text
data/processed/
└─ books_pages_001_003_processed_20260810_081501.csv
```

50페이지를 처리한 경우:

```text
books_pages_001_050_processed_YYYYMMDD_HHMMSS.csv
```


## 8. 프로젝트 설계 원칙

이 프로젝트는 다음 원칙을 기준으로 구성합니다.

- 원본 데이터는 수정하지 않고 `raw`에 보관합니다.
- 한 번의 수집 실행을 하나의 배치로 관리합니다.
- `raw`와 `interim`은 동일한 배치 이름을 사용합니다.
- 페이지별 원본 HTML과 parsed CSV를 유지합니다.
- 페이지별 parsed CSV는 전처리 단계에서 하나의 DataFrame으로 통합합니다.
- 전처리가 완료된 데이터만 `processed`에 저장합니다.
- 데이터 저장 전 필수 컬럼, 결측값, 중복값과 값의 범위를 검증합니다.
- 데이터베이스 비밀번호와 같은 민감한 정보는 `.env`로 분리합니다.
- `main.py`는 각 단계의 실행 함수를 연결하는 진입점 역할만 담당합니다.


## 9. 전체 파이프라인

현재 파이프라인의 실행 함수 연결 관계는 다음과 같습니다.

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
  │      ↓
  │   parsed_csv_files[0].parent
  │      ↓
  │   interim_batch_dir
  │
  ├─ run_preprocess(interim_batch_dir)
  │      ↓
  │   processed_csv_file
  │
  └─ run_load(processed_csv_file)
         ↓
      load_summary
```

데이터 처리 관점에서는 다음 흐름입니다.

```text
HTML
↓
페이지별 Parsed CSV
↓
통합된 Processed CSV
↓
MySQL
```

ETL 관점에서는 다음과 같이 구분할 수 있습니다.

```text
Extract
├─ 웹페이지 요청
├─ 원본 HTML 저장
└─ HTML 파싱

Transform
├─ 페이지별 CSV 통합
├─ 문자열 정리
├─ 자료형 변환
├─ 중복 처리
├─ 메타데이터 생성
└─ 데이터 검증

Load
├─ processed CSV 읽기
├─ 배치 정보 검증
├─ MySQL 연결
└─ INSERT / UPDATE
```

전체적으로 다음 ETL 흐름을 구성합니다.

```text
Extract → Transform → Load
```
