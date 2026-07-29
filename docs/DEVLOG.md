# PulseGrid — DEVLOG

> 세션별 개발 회고 및 트러블슈팅 기록

이 문서는 마일스톤 문서(`05_milestones.md`)처럼 "계획"을 담는 곳이 아니라, **실제로 각 세션에서 무슨 일이 있었는지**를 기록하는 곳이다. 막혔던 지점, 해결한 방법, 다음에 참고할 만한 실수 등을 가감 없이 남긴다.

---

## 작성 규칙

- 세션(하루 작업 단위) 종료 시 또는 마일스톤 완료 시 기록
- 최신 항목이 위로 오도록 역순 정렬
- 형식: 날짜 / 관련 마일스톤 / 한 일 / 막혔던 점 / 다음에 할 일

---

## 2026-07-28 — M0 완료, 기획 문서 작성, GitHub 초기 세팅

**관련 마일스톤**: M0 (환경 구성) → 기획 단계

**한 일**
- LibreHardwareMonitor 설치 (노트북 + 데스크탑)
  - 최신 버전은 `PawnIO` 드라이버를 요구함 (구버전 `WinRing0` 대체)
- Remote Web Server 활성화 후 `http://localhost:8085/data.json` 응답 확인
- 기획 문서 5종 + README + `.gitignore` 작성
  - `01_requirements.md`, `02_architecture.md`, `03_api_spec.md`, `04_ui_design.md`, `05_milestones.md`
- 로컬 Git 저장소 초기화 → 첫 커밋 → GitHub 원격 저장소(`sagming40/pulsegrid`) 연결 및 push 완료

**막혔던 점 / 트러블슈팅**
- 노트북 쪽 LibreHardwareMonitor에서 `data.json`이 안 뜨는 문제 발생
  - 원인: `Options → Remote Web Server → Run` 체크 안 되어 있었음 (데스크탑은 켜져 있었는데 노트북만 놓침)
  - 교훈: 여러 기기에 같은 설정을 반복할 때는 체크리스트로 비교하며 진행할 것

**다음에 할 일**
- M1 시작: LibreHardwareMonitor JSON에서 CPU/GPU/RAM 값만 추출하는 Python 수집기 프로토타입 작성

---

## 2026-07-29 — M1 완료: 수집기 프로토타입

**관련 마일스톤**: M1 (수집기 프로토타입) → 완료

**한 일**
- LibreHardwareMonitor JSON 재귀 탐색 함수(`find_by_sensor_id`) 구현
- SensorId 기반 매핑 테이블(`SENSOR_MAP`)로 CPU/GPU/RAM 값 추출
- API 명세서 MetricPayload 형식으로 변환 후 2초 간격 터미널 출력 확인

**막혔던 점 / 트러블슈팅**
- Text(이름)로 센서를 찾으려 하니 GPU Core(RTX 5070 vs 내장그래픽), Memory(실RAM vs 가상메모리) 등 이름 중복 문제 발생 → SensorId(고유 경로) 기반으로 변경
- RAM 사용률이 계속 None으로 나와 진단 함수까지 만들었는데, 알고 보니 SENSOR_MAP 값을 실험적으로 바꾸다 생긴 오타(`/ram/load/1` → `/ram/load/0`)가 원인이었음
- 교훈: 문제 원인 파악할 땐 여러 곳을 동시에 바꾸지 말고 한 번에 하나씩 검증할 것

**다음에 할 일**
- M2 시작: FastAPI 서버 구축, `POST /api/v1/metrics` 구현, WebSocket 브로드캐스트

---

## 2026-07-29 — M2 완료: 서버 + 단일 기기 연동

**관련 마일스톤**: M2 (서버 + 단일 기기 연동) → 완료

**한 일**
- FastAPI 서버 기본 구조 세팅 (`server/main.py`), uvicorn 실행 확인
- Pydantic `MetricPayload` 모델 정의 (`server/models.py`) — Cpu/Gpu/Ram/Disk/BatteryMetric 하위 모델 + 필수/선택 필드 구분
- `POST /api/v1/metrics` 구현, `device_id` 키 딕셔너리(`latest_metrics`)에 최신 상태 저장
- `WS /ws/dashboard` 구현 — 연결 시 `snapshot` 전송, 데이터 수신 시 전체 클라이언트에 `metric_update` 브로드캐스트
- `agent.py`에 서버 전송 로직(`requests.post`) 추가
- `web/index.html` 최소 페이지 작성, WebSocket으로 CPU 값 실시간 표시
- 브라우저 + agent.py 동시 실행으로 2초 간격 자동 갱신 확인 → M2 완료 기준 충족

**막혔던 점 / 트러블슈팅**
- `app = FastAPI` 괄호 누락 → `TypeError: FastAPI.get() missing 1 required positional argument`
- `WebSocket`을 `WecSocket`으로 오타 → `ImportError`
- WebSocket 연결이 계속 실패 → `websockets` 라이브러리 미설치가 원인 (fastapi/uvicorn 설치만으론 부족)
- `models.py` 파일을 `model.py`(단수)로 잘못 생성했다가 뒤늦게 발견 → 커밋 전이라 파일명만 정정 후 재작업
- agent.py에 서버로 POST 전송하는 코드가 없다는 걸 뒤늦게 인지 → `requests.post()` + `try/except`로 추가
- 교훈: 새 라이브러리(FastAPI 등)로 기능 확장할 때는 "관련 하위 패키지가 따로 필요할 수 있다"는 점을 염두에 둘 것

**다음에 할 일**
- M3 시작: agent 설정 파일 분리(`device_id`, 서버 주소), 노트북에서 동일 코드 실행, 서버 측 기기별 `online`/`offline` 판정 로직 추가

---
