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

## 2026-08-01 — M6 완료: 확장 지표 (디스크/배터리)

**관련 마일스톤**: M6 (확장 지표) → 완료

**한 일**
- config.json에 disk_map(배열 구조, id/label/primary/usage_sensor/temp_sensor)과 battery_sensor 추가 — 디스크 개수가 기기마다 다른 점을 고려해 처음부터 리스트로 설계, 노트북엔 battery_sensor만 추가
- 03_api_spec.md: MetricPayload의 disk 필드를 객체 → 배열로 변경, label 필드 추가, 관련 예시 3곳(3.1/3.2/4.2) 모두 실제 payload 구조로 수정
- server/models.py: DiskMetric에 id/label 필드 추가, MetricPayload.disk를 Optional[list[DiskMetric]]로 변경
- agent/agent.py: disk_map을 순회하며 디스크별 사용률/온도/라벨 파싱, battery_sensor 유무에 따라 분기 처리(없는 기기는 battery: null)
- server/schema.sql, db.py: device_metrics_history에 battery_level/battery_charging 컬럼 추가(ALTER TABLE로 기존 DB에도 적용), disk 배열 중 id="main"인 항목을 대표로 골라 저장하도록 save_metric_snapshot() 수정
- web/app.js, style.css: 카드 하단 디스크 영역을 고정 한 줄(span)에서, 디스크 개수만큼 줄을 동적으로 그리는 컨테이너(div.disk-summary-list) 구조로 변경
- (M6 완료 기준엔 없었으나 뒤이어 진행) 디스크 표시를 "id" 대신 사용자 지정 label(`C: (SSD 1TB)` 형식)로 바꾸고 온도도 함께 렌더링하도록 개선, 구분자를 앱 전체 표준인 "·"로 통일. 04_ui_design.md 3.1-b절에 디스크 표시 형식 규격 신설
- 데스크탑(디스크 2개)·노트북(디스크 1개+배터리) 양쪽 실 데이터로 최종 검증 완료

**막혔던 점 / 트러블슈팅**
- db.py의 save_metric_snapshot()이 disk를 여전히 단일 객체로 취급하고 있어 disk를 배열로 바꾼 직후 `'list' object has no attribute 'usage'` 에러 발생 — Task 6-3에서 "id=='main'인 항목을 대표로 골라 저장"하는 로직으로 수정 (예상된 순서상의 에러)
- 노트북에서 agent.py 실행 시 disk/battery가 계속 null로 나오는 문제 발생 — config.json은 정상이었으나, 데스크탑에서만 agent.py를 수정하고 커밋 전이라 노트북의 agent.py가 예전 버전 그대로였던 게 원인. 여러 기기에 같은 코드가 물리적으로 따로 존재하며, 커밋 전엔 다른 기기로 자동 반영되지 않는다는 점을 재확인
- 배터리 충전 여부(charging) 판정을 위해 충전기 연결 전/후 LibreHardwareMonitor 값을 비교했으나, 배터리가 이미 98~99%로 거의 완충 상태라 두 캡처 모두 "Discharge Rate"로 표시되어 판정 근거를 얻지 못함 → 부정확한 값을 무리하게 만들기보다 charging은 항상 null로 보류하기로 결정
- 03_api_spec.md의 disk 배열 JSON 예시 3곳에 config.json의 disk_map 원본 필드(primary, usage_sensor, temp_sensor)가 그대로 복사되어 들어가는 실수 발생 — 실제 API payload와 config 전용 필드를 혼동한 것으로, 검수 단계에서 발견해 실제 payload 구조(id/label/usage/temp)로 수정
- 디스크 라벨 표기법(`=`/`—`/`→` 등) 고민 끝에, 앱 전체에서 이미 쓰고 있던 구분자 "·"로 통일 — 화면 안에서 구분 기호를 하나로 맞추는 게 가독성에 유리함을 확인
- 교훈: 여러 기기에서 동시에 코드를 고칠 땐, 한쪽에서 먼저 커밋·push하고 나머지 기기는 pull(또는 discard 후 pull)로 맞추는 편이 혼란을 줄여줌

**다음에 할 일**
- M6.5(가칭 — 히스토리 히트맵 + 날씨 API 연동) 또는 M7(문서화/배포 정리) 진행 예정, 마일스톤 번호는 실제 착수 시점에 확정

---

## 2026-08-02 — M6.5 완료: 시각화 확장 (히트맵 + 전력 + 테마)

**관련 마일스톤**: M6.5 (시각화 확장) → 완료

**한 일**
- **A그룹(히트맵)**: `HOUR(recorded_at)` 기준 GROUP BY로 기기별/시간대별 CPU 평균 집계하는 `get_heatmap()` 구현, `GET /api/v1/heatmap` 엔드포인트 추가, 프론트엔드에 기기별 24칸 그리드로 렌더링(desktop/laptop 2줄)
- **B그룹 범위 변경**: 원래 계획이던 "외부 날씨 API 연동"을 재검토 — "PC 하드웨어 모니터링 대시보드에 날씨가 왜 있나"라는 정체성 문제 + 데스크탑 카드 하단에 배터리 대응 지표가 없어 허전해 보이던 UI 문제(직접 관찰)를 계기로, **CPU+GPU 실시간 전력(W) 표시**로 대체. LibreHardwareMonitor의 `Power` 타입 센서 확인 후 config.json/models.py/agent.py에 파싱 추가, 히스토리 테이블에 cpu_power/gpu_power 컬럼 추가, 카드 우측 하단에 전력+배터리를 세로로 나란히 배치
- **C그룹(테마)**: style.css 전체를 CSS 변수로 리팩터링(기능 변화 없는 순수 리팩터링 커밋 분리) → `prefers-color-scheme` 기반 시스템 연동 다크모드 → 톱니바퀴 버튼 + 드롭다운(시스템/라이트/다크) 수동 전환 + `localStorage` 저장까지 구현
- 원래 B그룹이 노렸던 "외부 REST API + 서버 캐싱" 학습 목표는 버리지 않고, 별도 마일스톤 **M8(전국 전력수급 API 연동)**으로 분리해 이어가기로 결정 (M7 이후 진행)

**막혔던 점 / 트러블슈팅**
- 히트맵 색상을 반투명(rgba) 방식으로 구현했더니 다크모드 배경에서 진하기 차이가 거의 안 보이는 문제 발견 — 반투명은 배경색에 의존하는 방식이라, 배경이 이미 어두우면 대비가 묻힘. "두 색상 끝점을 직접 보간(interpolation)"하는 방식으로 교체해 해결
- 색상 자체도 보라 계열은 인간 눈이 명암 차이를 둔감하게 느끼는 대역이라 대비 개선 후에도 잘 안 보임 → 주황/크림 계열로 재변경
- 고정된 0~100% 스케일로 색을 매핑하다 보니, 실사용 범위(대부분 5~20%)에서는 서로 다른 값이어도 색 차이가 거의 안 보이는 문제 → 히트맵 데이터 내 실제 최댓값을 기준으로 스케일을 동적으로 재조정하도록 수정
- `git commit --amend`로 이전 커밋 메시지(접두사 누락)를 수정하고 `--force-with-lease`로 push했는데, 그 시점에 이미 노트북이 예전 커밋을 pull해간 상태였음 — 노트북에서 다시 pull하니 "같은 내용, 다른 커밋"으로 인식되어 자동 병합 커밋이 하나 발생. 충돌 없이 자동 병합되어 실제 코드 손상은 없었으나, 히스토리가 두 기기에서 일시적으로 어긋남 → 노트북 push → 데스크탑 pull 순서로 재동기화. 교훈: 이미 다른 기기가 pull해간 커밋은 amend하지 말 것, 부득이하면 amend 직후 바로 다른 기기부터 동기화할 것
- SQL `INSERT` 문 작성 중 `VALUES (...)`의 마지막에 콤마가 하나 더 붙어 `mariadb.ProgrammingError` 발생 — 컬럼 추가할 때마다 `%s` 개수와 콤마 위치를 한 번 더 세어보는 습관 필요
- 다크모드 전환 시 배경은 즉시 바뀌는데 히트맵 색은 그대로 남아있는 문제 발견 — 원인은 히트맵이 "페이지 로드 시점"에 CSS 변수를 딱 한 번 읽어서 고정된 색상값을 셀에 박아넣는 구조였기 때문. 테마 토글 기능에서 `applyTheme()`이 `loadHeatmap()`을 재호출하도록 연결해 해결(단, OS 설정 자체를 직접 바꾸는 경우는 여전히 새로고침 필요)

**다음에 할 일**
- M7(문서화/배포 정리) 진행 — README, 스크린샷, `03_api_spec.md`에 heatmap 엔드포인트 반영, `requirements.txt` 정리 등
- M7 이후 M8(전국 전력수급 API 연동) 진행 예정

---

## 2026-08-12 — M7 완료: 문서화 / 배포 정리

**관련 마일스톤**: M7 (문서화/배포 정리) → 완료

**한 일**
- **Task 7-1 (의존성/설정 정리)**: `requirements.txt`, `db_config.example.json`은 이미 최신 상태임을 확인. `agent/config.example.json` 단일 파일을 `config.example.desktop.json`/`.laptop.json`으로 분리. `requirements.txt`가 PowerShell 리다이렉션(`pip freeze > requirements.txt`) 과정에서 UTF-16으로 잘못 저장돼 있던 것을 발견해 UTF-8로 재저장
- **Task 7-2 (`03_api_spec.md` 실제 구현 반영)**: cpu/gpu에 `power` 필드 추가, `history` 쿼리 파라미터를 `from`/`to`/`metric` → `device_id`/`minutes`로 갱신(응답 구조도 함께 변경), `heatmap` 엔드포인트 신규 문서화, `devices`/`devices/{id}`/`health`를 미구현으로 명시(사유 기록). 문서 검수 과정에서 `get_history()`의 `SELECT` 절에 `cpu_power`/`gpu_power`가 누락돼 DB엔 저장되지만 조회 응답엔 안 나오던 버그를 발견해 수정
- **Task 7-3 (README 전면 개정)**: MariaDB 설치/`schema.sql` 실행/`db_config.json` 설정 순서를 신설, config 파일 분리 반영, API 개요·프로젝트 구조·개발 로드맵·개발 환경 갱신, `LICENSE`(MIT) 신규 추가
- **Task 7-4 (스크린샷/GIF)**: 메인 대시보드(PNG), 실시간 갱신·히스토리 모드 전환·라이트/다크 테마 전환(GIF) 총 4종 캡처, `docs/images/` 폴더 신설 후 README에 삽입(테마/히스토리는 `<details>` 접이식 블록으로 배치)
- **Task 7-5 (클린룸 검증)**: 노트북에 완전히 새 폴더로 클론해 README만 보고 처음부터 재현. 아래 4가지 문제 발견 및 수정

**막혔던 점 / 트러블슈팅**
- `mysql -u root -p < schema.sql`이 PowerShell에서 `The '<' operator is reserved for future use` 오류로 실패 — cmd.exe/Git Bash에서만 되는 리다이렉션 문법이었음. `Get-Content schema.sql | mysql -u root -p` 파이프 방식으로 교체, README에도 반영
- MariaDB 설치 후 `mysql` 명령어가 인식되지 않음 — 설치 경로의 `bin` 폴더가 시스템 PATH에 자동 등록되지 않는 경우가 있음을 확인. README "데이터베이스 준비" 섹션에 `mysql --version`으로 사전 확인하고, 안 되면 PATH를 직접 추가하라는 안내 신설
- `schema.sql` 실행 시 `ERROR 1046: No database selected` — `CREATE DATABASE`만 있고 `USE pulsegrid;`가 빠져 있어, CLI로 스크립트 전체를 실행하면 테이블을 어느 DB에 만들지 지정되지 않는 문제였음. HeidiSQL로 DB를 미리 선택해두고 작업했던 이전 세션에서는 드러나지 않았던 버그. `schema.sql`에 `USE pulsegrid;` 한 줄 추가로 수정
- agent `config.json`의 `server_url`/`device_name`/`sensor_map` 값을 "어떻게" 채우는지 README에 절차가 전혀 없어, 처음 보는 입장에서는 막막한 지점이었음. 특히 `server_url`에 `127.0.0.1`을 그대로 넣으면 다른 기기에선 절대 서버를 못 찾는다는 점(자기 자신을 가리키는 특수 주소)을 명확히 설명하지 않았던 것이 가장 위험한 공백이었음 — 에러 메시지 없이 조용히 연결만 안 되는 유형이라 원인 추적이 어려움. README에 `ipconfig`로 IP 확인하는 법, `data.json`에서 `device_name`/SensorId 찾는 법(검색 키워드 표 포함)을 상세히 추가
- 위 4가지 모두 **데스크탑 하나로만 개발할 땐 절대 드러나지 않았을 문제들**이었음. 개발자 본인 환경은 이미 모든 게 세팅된 상태라 "처음 겪는 막막함"을 재현할 수 없다는 걸 체감

**교훈**
- 클린룸 검증은 "형식적인 마지막 단계"가 아니라, 이번 세션에서 발견한 문제 4개 중 3개가 **문서만 봐서는 절대 못 잡는 종류**(터미널 종류 차이, 환경변수, 실행 순서 의존성)였음. 코드 리뷰나 API 스펙 검수와는 완전히 다른 종류의 검증이라는 걸 확인
- "완료 기준"을 "README만 보고 실행 가능한 상태"처럼 구체적으로 적어두면, 그 기준을 실제로 시험해볼 방법(클린룸)도 자연히 따라온다는 걸 체감 — 애매한 완료 기준이었다면 이런 문제들을 못 찾았을 것

**다음에 할 일**
- M7 완료로 v1.0 이후 계획했던 P1 항목(M5~M7) 전부 완주
- M8(공공데이터포털 전국 전력수급 현황 API 연동) 진행 예정

---
