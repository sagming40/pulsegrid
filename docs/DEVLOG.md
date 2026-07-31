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

## 2026-07-29 — M3 완료: 다중 기기 연동

**관련 마일스톤**: M3 (다중 기기 연동) → 완료

**한 일**
- agent 설정값(`device_id`, `device_name`, `server_url`, `sensor_map`)을 `config.json`으로 분리, `config.example.json` 추가 (Git 추적)
- 노트북(Intel i7-1255U / Iris Xe) 센서 SensorId 매핑 완료 — CPU는 `/intelcpu/0/...`, GPU는 `/gpu-intel-integrated/...`(내장그래픽은 온도 센서 없어 `null` 처리)
- 노트북에서 `agent.py` 실행 → 데스크탑 서버로 데이터 전송 성공
- 서버에 `last_seen`(기기별 마지막 수신 시각), `device_status`(online/offline) 딕셔너리 추가
- `lifespan` + `asyncio.create_task`로 서버 시작 시 백그라운드 순찰 작업(`patrol_offline_devices`) 등록 — 3초 주기로 각 기기의 마지막 수신 시각 확인, 10초 초과 시 offline 전환 및 `device_status` 브로드캐스트
- `web/index.html`을 기기별 카드 구조로 개편 (`getOrCreateCard`) — `snapshot`/`metric_update`/`device_status` 메시지 모두 처리
- 데스크탑+노트북 동시 실행으로 최종 검증: 한쪽만 꺼도 다른 쪽 상태에 영향 없이 독립적으로 online/offline 판정됨을 확인

**막혔던 점 / 트러블슈팅**
- `collect_metrics()` 리팩터링 중 함수 시그니처(매개변수)는 안 고치고 몸통/주석만 고쳐서 `TypeError` 발생 → 리팩터링 시 시그니처와 몸통을 함께 확인할 것
- `config.example.json`만 만들고 실제 `config.json` 생성을 빼먹어 `FileNotFoundError` 발생
- 노트북에서 서버로 접속 시 `TimeoutError` 발생 → 원인은 `uvicorn`이 기본값(`127.0.0.1`)으로만 열려 있었던 것. `--host 0.0.0.0`으로 해결
- `web/index.html`의 WebSocket 주소가 `127.0.0.1`로 하드코딩되어 있어 노트북에서 페이지를 열면 자기 자신에게 연결 시도 → `window.location.hostname`으로 동적 처리하여 해결
- 서버 쪽 브로드캐스트 메시지 타입에 오타(`devices_status` vs `device_status`) 발생 — 같은 메시지를 두 곳(receive_metrics, patrol_offline_devices)에서 만들다 보니 한쪽만 놓침. 코드 검수 단계에서 발견
- 교훈: 서로 다른 컴퓨터가 통신할 때는 `127.0.0.1`(자기 자신)과 실제 네트워크 IP를 명확히 구분해야 함. agent, 서버, 프론트엔드 세 군데 모두에서 이 실수가 반복됐음

**다음에 할 일**
- M4 시작: 기기 카드 UI 정식 구현(게이지 바, 온도별 색상 경고), Chart.js 실시간 추이 그래프, 반응형 레이아웃, WebSocket 자동 재연결

---

## 2026-07-31 — M4 완료: 대시보드 완성 → v1.0 릴리즈

**관련 마일스톤**: M4 (대시보드 완성) → 완료, v1.0 릴리즈 범위(M1~M4) 완주

**한 일**
- 기기 카드를 04_ui_design 3장 규격대로 정식화 — 아이콘/표시이름/호스트명/상태배지/지표행(CPU·GPU·RAM)/하단요약(디스크·배터리) 구조로 개편, null 값은 자리 유지한 채 대시(—)로 표시
- 사용률(정상~74% / 주의 75~89% / 위험 90%~), 온도(정상~69°C / 주의 70~84°C / 위험 85°C~) 3단계 임계치에 따라 게이지 바 색상과 온도 텍스트 색상을 JS로 갈아 끼우도록 구현
- Chart.js로 기기별 CPU 사용률 실시간 추이 그래프 추가 — 여러 기기가 서로 다른 타이밍에 데이터를 보내도 그래프 틱은 최소 1.8초 간격으로만 찍히도록 기록계 로직 별도 구현, 최근 30포인트(약 60초)만 유지
- `#cards-container`를 flex에서 CSS Grid(`auto-fit` + `minmax`)로 전환해 반응형 레이아웃 적용
- WebSocket 연결 끊김 감지 시 헤더에 상태 배지(실시간 연결/연결 끊김) 표시, `onclose` 핸들러에서 3초 후 자기 자신을 재호출하는 방식으로 자동 재연결 구현
- 테스트 과정에서 발견한 사이드 버그 2건도 함께 수정
  - Chart.js가 `maintainAspectRatio` 옵션과 `<canvas>` 고정 height 속성을 동시에 갖고 있어 DevTools 토글 등 급격한 리사이즈 시 그래프가 찌그러진 채 복구 안 되던 문제 → `maintainAspectRatio: false` + 고정 높이 wrapper div로 해결
  - 새로고침 시 WebSocket `snapshot` 메시지에 `status` 필드가 아예 없어서 상태배지에 `undefined`가 찍히던 문제 → 서버에서 `device_status` 딕셔너리를 참조해 snapshot 데이터에 `status`를 채워 넣도록 수정

**막혔던 점 / 트러블슈팅**
- Chart.js dataset 초기화 코드에서 `data: deviceId`(문자열)로 잘못 넣어서 그래프가 안 그려짐 → `data: []`(빈 배열)로 시작해야 한다는 걸 놓침
- 같은 함수에서 `dataset.data.push(...)` 줄 자체가 통째로 누락되어, "30개 넘으면 오래된 거 지우기" 로직만 있고 정작 "새 값 넣기"가 없었던 상태로 한동안 방치됨 — 코드 검수 단계에서 발견
- 커밋을 여러 Task로 나누는 과정에서, 이미 다른 Task(4-4) 작업 위에 별개의 버그 수정 두 건이 함께 쌓여 뒤섞인 적 있음 → GitHub Desktop 부분 스테이징(줄 단위 체크)으로 재분리해서 커밋 단위를 다시 맞춤
- 커밋 메시지에 Task 번호(`M4 Task 4-4` 등)를 붙이는 기준을 명확히 함 — 계획에 있던 작업 항목에만 Task 번호를 붙이고, 테스트 중 우연히 발견한 사이드 버그 수정에는 Task 번호를 붙이지 않기로 정리
- 교훈: Chart.js처럼 라이브러리가 제공하는 "자동" 옵션(`maintainAspectRatio` 등)은 컨테이너 크기 관리 방식과 충돌할 수 있으니, 라이브러리 기본값을 그대로 쓰기보다 컨테이너 쪽 크기를 명시적으로 고정하는 편이 안전함

**다음에 할 일**
- v1.0 릴리즈 범위(M1~M4) 완주. M5(히스토리 저장) / M6(확장 지표) / M7(문서화) 중 순서 자유롭게 진행 예정

---

**기타 메모**
> `web/index.html`에 HTML+CSS+JS를 한꺼번에 담게 된 배경

- 프로젝트 기획 시 처음 설계했던 폴더 구조(`web/style.css`, `web/app.js` 분리)를 따르지 않고, 한 파일에 담게 된 이유를 돌아봄
- M2 시작 시점엔 "최소 HTML 페이지" 목표라 파일 하나가 합리적이었음
- 이후 M3~M4에서 매번 "기존 코드에 이어붙이기" 방식으로 진행하다 보니 파일을 나눌 계기가 없었음
- 1인 프로젝트라 협업 충돌 이슈도 없어 지금까지는 문제 없었음
- M7(문서화/배포 정리)에서 `<style>`은 `web/style.css`로, `<script>`는 `web/app.js`로 분리해 원래 계획했던 구조와 맞출 예정

---

## 2026-07-31 — M5 완료: 히스토리 저장

**관련 마일스톤**: M5 (히스토리 저장) → 완료

**한 일**
- MariaDB Connector/C 3.4.9(Complete) 설치, `mariadb` 파이썬 드라이버 연동
- `device_metrics_history` 테이블 설계 — CPU/GPU/RAM/Disk를 평탄화된 컬럼으로, `device_id + recorded_at` 복합 인덱스 추가 (`server/schema.sql`)
- `server/db.py` 작성 — `save_metric_snapshot()`(1분 간격 저장), `get_history()`(기간 조회)
- `main.py` lifespan에 `save_history_periodically()` 백그라운드 태스크 등록, `device_status`가 `online`인 기기만 저장하도록 조건 추가 (offline 기기 값이 무한 복제되던 문제 방지)
- `GET /api/v1/history?device_id=&minutes=` 엔드포인트 구현, 기존 API 공통 응답 형식(`success`/`data`/`error`) 그대로 적용
- `web/index.html`의 `<style>`/`<script>`를 `web/style.css`/`web/app.js`로 분리 (원래 M7 예정 작업이었으나 선행 처리), `main.py`에 `StaticFiles` 마운트 추가
- 프론트엔드에 "기기"/"기간"(실시간·1시간·6시간·24시간) 드롭다운 추가 — 기간 선택 시 `GET /api/v1/history` 호출해 과거 기록으로 그래프 교체, 실시간 선택 시 기존 다중 기기 실시간 그래프로 복귀
- 데스크탑+노트북 양쪽 기기로 저장/조회/모드 전환 전체 흐름 검증 완료

**막혔던 점 / 트러블슈팅**
- `db.py` 작성 중 `json.load(f)`를 `json,load(f)`로 오타 → `NameError`
- `save_history_periodically()`에 online 여부 확인 로직이 빠져있어, agent를 꺼도 서버가 마지막 값을 무한정 복제 저장하는 버그 발견 → `device_status` 체크 추가로 수정. 단, `patrol_offline_devices`의 offline 판정에 최대 13초 유예가 있어 그 사이 중복 스냅샷이 최대 1개 발생할 수 있음 — 허용 가능한 범위로 판단하고 넘어감
- `index.html`/`style.css`/`app.js` 분리 직후 정적 파일 404 발생 → `main.py`에 `StaticFiles` 마운트가 없었던 게 원인, 다른 라우트들 밑에 `app.mount("/", StaticFiles(...))` 추가로 해결
- `loadHistoryChart(deviceId, Number(range))`에서 콤마를 마침표로 오타 → `TypeError`
- 실시간 모드에서 "기기" 드롭다운을 골라도 아무 반응이 없어 조작 가능한 것처럼 보이는 UX 문제 발견 → 실시간 모드에선 드롭다운을 `disabled` 처리하도록 수정
- 교훈: `json,load`, `deviceId. Number` 등 마침표/콤마 오타가 두 번 반복됨 — 타이핑 후 한 번 더 훑어보는 습관 필요

**다음에 할 일**
- M6(확장 지표) 또는 M7(문서화/배포 정리) 중 진행 예정

---

**기타 메모**
> `03_api_spec.md`에 설계된 `GET /api/v1/devices`, `/api/v1/devices/{id}`, `/api/v1/health`를 구현하지 않은 이유

- 세 엔드포인트 모두 2026-07-28 기획 단계에서 설계했으나, M2~M4를 거치며 실제로 만들 필요가 없어짐
- `/devices`, `/devices/{id}`: M2에서 `WS /ws/dashboard`를 설계할 때 "연결 직후 `snapshot` 메시지로 전체 기기 최신 상태 전송"을 이미 포함시켰음 — REST로 초기 조회 후 WebSocket 연결하는 2단계 흐름 대신, WebSocket 하나로 초기 상태+실시간 갱신을 모두 처리
  - REST+WS 병행 시 "REST 응답 시점과 WebSocket 연결 시점 사이의 데이터 갱신을 놓칠 수 있는" 동기화 문제를 애초에 피할 수 있었음
  - `latest_metrics` 딕셔너리를 유일한 진실 공급원으로 유지할 수 있어 서버/프론트엔드 양쪽 로직이 단순해짐
- `/health`: 외부 모니터링 도구 연동을 계획했던 용도인데, 1인 개인 프로젝트 특성상 아직 그런 외부 모니터링 자체가 없어 필요성이 생기지 않음. M8(Flutter 모바일 클라이언트) 등에서 연결 확인 용도로 필요해지면 그때 재검토
- `03_api_spec.md`는 계획 문서 성격이라 지금 당장 수정하지 않고, M6/M7 문서 정리 단계에서 실제 구현 현황에 맞게 갱신 예정 (`history` 엔드포인트의 쿼리 파라미터가 `from`/`to`/`metric`에서 `minutes`로 단순화된 것도 함께 반영)

---
