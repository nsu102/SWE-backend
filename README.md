# SWE Backend

상의 사진에서 옷 영역을 추출하고 FashionCLIP 임베딩으로 유사 상품을 검색하는 독립 백엔드 저장소입니다. 상품 원본은 로컬 또는 S3에 둘 수 있고, 상품 정보와 512차원 벡터는 PostgreSQL + pgvector에 저장합니다.

## 구성

```text
src/backend/              FastAPI, ML 추론, PostgreSQL, 이미지 URL
src/jobs/index_catalog.py 크롤링 결과 임베딩 및 DB 적재
src/common/               사람/상의 파싱 공통 코드
deploy/backend/           EC2 + RDS 배포 파일
tests/                    단위 테스트
```

## 로컬 실행

Python 3.12 기준입니다.

```bash
python3 -m venv work/.venv
work/.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
work/.venv/bin/pip install -r requirements-backend.txt -r requirements-ml.txt -r requirements-aws.txt
cp .env.example .env
make db-up
```

로컬 DB는 `pgvector/pgvector:pg16` 컨테이너로 실행되며 `127.0.0.1:5432`에서만 접근할 수 있습니다. 최초 볼륨 생성 시 `src/backend/schema.sql`이 자동 실행되어 `vector` 확장, 상품·검색 이력 테이블과 HNSW 인덱스를 만듭니다.

```bash
make db-status # 상태 확인
make db-shell  # psql 접속
make db-logs   # DB 로그
make db-down   # 컨테이너 중지, 데이터 볼륨 유지
make db-reset  # 데이터 볼륨 삭제 후 완전 초기화
```

기본 로컬 접속 정보는 다음과 같습니다.

```text
host: 127.0.0.1
port: 5432
database: fashion
user: fashion
password: fashion
DATABASE_URL: postgresql://fashion:fashion@localhost:5432/fashion
```

포트나 계정을 바꾸려면 `.env`의 `POSTGRES_*`와 `DATABASE_URL`을 함께 변경해야 합니다. 이 값은 로컬 개발 전용이며 운영 DB 비밀번호로 재사용하면 안 됩니다.

`.env`를 현재 셸에 적용한 뒤 API를 실행합니다.

```bash
set -a
source .env
set +a
work/.venv/bin/uvicorn src.backend.app:app --host 127.0.0.1 --port 8000 --reload
```

- API 문서: `http://127.0.0.1:8000/docs`
- 생존 확인: `GET /health/live`
- DB 포함 상태 확인: `GET /health`
- 이미지 검색: `POST /api/search?limit=20&platform=musinsa`
- 상품 이미지: `GET /media/{platform}/{goods_no}`

## 크롤링 결과 적재

크롤러 저장소가 만든 `products.csv`와 `selected/selections.jsonl`을 명시적으로 전달합니다. `selections.jsonl`에 `s3_bucket`과 `s3_key`가 있으면 S3에서 직접 이미지를 읽고, 로컬 파일만 있으면 `storage/`에 복사합니다.

```bash
work/.venv/bin/python -m src.jobs.index_catalog \
  --platform musinsa \
  --products ../SWE-crawl/data/musinsa/tops/products.csv \
  --selections ../SWE-crawl/data/musinsa/tops/selected/selections.jsonl \
  --limit 5
```

`--limit`을 제거하면 선택 완료 상품 전체를 upsert합니다. EC2에서는 access key를 파일에 넣지 말고 S3 읽기 권한이 있는 IAM Role을 인스턴스에 연결하는 방식을 권장합니다.

## EC2/RDS 배포

`deploy/backend/env.example`을 `deploy/backend/.env`로 복사하고 RDS 주소, 프런트엔드 도메인, S3 버킷을 입력합니다. RDS는 PostgreSQL 16과 pgvector 확장을 사용할 수 있어야 합니다.

```bash
cd deploy/backend
./deploy.sh
```

Nginx는 외부 요청을 API 컨테이너로 전달하고, API 컨테이너는 `127.0.0.1:8000`에만 노출됩니다. 상세 보안 그룹과 IAM 예시는 `deploy/backend/` 파일을 참고하세요.

## 주요 환경변수

| 이름 | 용도 |
| --- | --- |
| `DATABASE_URL` | PostgreSQL/RDS 접속 문자열 |
| `AUTO_MIGRATE` | 시작 시 스키마 생성 여부 |
| `AWS_BUCKET_NAME` | 상품 이미지 S3 버킷 |
| `AWS_REGION` | S3 리전 |
| `LOCAL_STORAGE_ROOT` | 로컬 상품 이미지 루트 |
| `CORS_ORIGINS` | 허용할 프런트엔드 origin 목록 |
| `MAX_UPLOAD_MB` | 검색 사진 최대 크기 |

실제 `.env`, 인증서, 모델 캐시, 로컬 저장 이미지는 Git에 포함되지 않습니다.
