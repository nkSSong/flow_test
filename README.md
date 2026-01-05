## 배포 정보 (Render)
본 프로젝트는 Render Free Web Service를 사용하여 실제 서비스 환경에 배포되어 있습니다.

배포 주소
https://flow-test-0vst.onrender.com

Render Free 플랜 관련 안내
	•	Render 무료 플랜 특성상 15분 이상 트래픽이 없을 경우 서버가 자동으로 sleep 상태로 전환됩니다.
	•	sleep 상태에서 최초 접속 시 서버 기동까지 약 5분 이상 소요될 수 있습니다.
	•	이는 정상적인 동작이며, 서버가 기동된 이후에는 정상적으로 서비스가 제공됩니다.

검증 시에는 접속 후 잠시 대기해주시면 됩니다.
## 설치 방법

1) 가상환경 생성 및 활성화

python -m venv .venv
source .venv/bin/activate

2) 패키지 설치

pip install fastapi uvicorn pytest httpx
## 실행 방법

uvicorn main:app –reload

브라우저 접속 주소
http://127.0.0.1:8000/
## 테스트 방법 (Pytest)

프로젝트 루트 디렉토리에서 실행

pytest

옵션별 실행 방법

pytest -q
pytest -vv
pytest -x

테스트 범위
	•	설정 조회 API(/api/config) 응답 구조 검증
	•	고정 확장자 체크/해제 시 DB 저장 및 유지 여부
	•	커스텀 확장자 추가 기능 검증
	•	커스텀 확장자 삭제 기능 검증
	•	커스텀 확장자 중복 등록 방지
	•	확장자 최대 길이(20자) 제한 검증
	•	커스텀 확장자 최대 200개 제한 검증
	•	고정 확장자와 커스텀 확장자 충돌 방지 검증

테스트 실행 시에는 임시 SQLite DB를 사용하여 실제 데이터가 오염되지 않도록 구성하였다.
## 프로젝트 스택
Backend
	•	Python 3.9
	•	FastAPI
	•	Uvicorn

Frontend
	•	HTML
	•	CSS
	•	Vanilla JavaScript

Database
	•	SQLite (파일 기반 DB)

Test
	•	Pytest
	•	FastAPI TestClient
## 기술 선택 이유
FastAPI 선택 이유
	•	과제 요구사항이 명확한 CRUD 중심 API이므로 간결하고 직관적인 구현이 가능한 FastAPI가 적합하다고 판단
	•	자동 API 문서(Swagger UI)를 제공하여 기능 검증 및 테스트가 용이
	•	TestClient를 통한 테스트 코드 작성이 쉬워 과제 완성도를 높일 수 있음

HTML + Vanilla JavaScript 선택 이유
	•	요구사항이 단순한 설정 관리 화면이므로 프론트엔드 프레임워크 사용은 과도하다고 판단
	•	별도의 빌드 과정 없이 서버 실행만으로 바로 화면 확인 가능
	•	리뷰어 및 면접관이 추가 환경 설정 없이 즉시 실행 가능

SQLite 선택 이유
	•	별도의 DB 서버 설치가 필요 없어 실행과 제출이 간편
	•	파일 기반 DB로 과제 제출 및 간단한 배포에 적합
	•	확장자 차단 설정 저장 및 유지 요구사항을 충족하기에 충분한 기능 제공
## 고려한 점
	•	입력값 정규화: 대문자 입력을 소문자로 변환하고 .sh 형태의 입력은 sh로 정규화
	•	중복 방지: 동일한 커스텀 확장자 재등록 시 에러 처리
	•	충돌 방지: 고정 확장자 목록에 포함된 확장자는 커스텀 확장자로 등록 불가
	•	유효성 검증: 확장자 최대 길이 20자 제한, 영문 소문자 및 숫자만 허용
	•	개수 제한: 커스텀 확장자 최대 200개까지 등록 가능
