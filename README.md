# PulseGrid

> 여러 대의 PC를 실시간으로 모니터링하는 웹 대시보드

노트북과 데스크탑처럼 사양이 서로 다른 여러 대의 PC의 CPU / GPU / RAM 상태를 한 화면에서 실시간으로 확인할 수 있는 개인용 모니터링 대시보드입니다.

> **개발 진행 중** — 현재 M3(다중 기기 연동) 완료, M4(대시보드 완성 → v1.0) 진행 예정
> 진행 상황은 [개발 일정 문서](docs/05_milestones.md)를 참고하세요.

<!-- TODO: 대시보드 스크린샷 또는 동작 GIF 삽입 -->

---

## 주요 기능

- **다중 기기 동시 모니터링** — 여러 대의 PC 상태를 한 화면에서 확인
- **실시간 갱신** — WebSocket 기반 2초 간격 자동 갱신
- **이기종 하드웨어 대응** — Intel / AMD / NVIDIA 등 제조사가 달라도 동일한 방식으로 수집
- **임계치 경고** — 온도 및 사용률이 기준을 넘으면 시각적으로 표시
- **오프라인 감지** — 기기가 꺼지거나 연결이 끊기면 자동 감지

---

## 시스템 구조

```
┌──────────────┐   ┌──────────────┐
│    노트북     │   │   데스크탑    │
│              │   │              │
│ LibreHardware│   │ LibreHardware│
│   Monitor    │   │   Monitor    │
│      ↓       │   │      ↓       │
│ PulseGrid    │   │ PulseGrid    │
│   Agent      │   │   Agent      │
└──────┬───────┘   └──────┬───────┘
       │  HTTP POST (2초)  │
       └─────────┬─────────┘
                 ↓
      ┌────────────────────┐
      │  PulseGrid Server  │
      │     (FastAPI)      │
      └─────────┬──────────┘
                │ WebSocket
                ↓
      ┌────────────────────┐
      │    웹 대시보드       │
      └────────────────────┘
```

| 구성 요소 | 역할 |
|---|---|
| LibreHardwareMonitor | 하드웨어 센서 값을 JSON으로 제공 (외부 도구) |
| PulseGrid Agent | 각 기기에서 센서 값을 수집해 서버로 전송 |
| PulseGrid Server | 데이터 수신 및 실시간 브로드캐스트 |
| 웹 대시보드 | 브라우저에서 실시간 상태 표시 |

자세한 설계 내용은 [시스템 아키텍처 문서](docs/02_architecture.md)를 참고하세요.

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| 센서 수집 | LibreHardwareMonitor |
| 수집기 | Python, `requests` |
| 백엔드 | Python, FastAPI |
| 실시간 통신 | WebSocket |
| 프론트엔드 | HTML, JavaScript, Chart.js |
| 데이터베이스 | MariaDB *(예정)* |

---

## 프로젝트 구조

```
pulsegrid/
├── agent/              # 각 기기에서 실행되는 수집기
│   ├── agent.py
│   └── config.example.json
├── server/             # FastAPI 서버
│   ├── main.py
│   ├── models.py
│   └── ...
├── web/                # 웹 대시보드
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/               # 설계 문서
│   ├── 01_requirements.md
│   ├── 02_architecture.md
│   ├── 03_api_spec.md
│   ├── 04_ui_design.md
│   └── 05_milestones.md
├── requirements.txt
└── README.md
```

> 구조는 개발 진행에 따라 변경될 수 있습니다.

---

## 시작하기

### 사전 준비

각 모니터링 대상 기기에 [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)를 설치하고 원격 웹 서버 기능을 활성화해야 합니다.

1. 최신 릴리즈에서 `LibreHardwareMonitor.zip` 다운로드 후 압축 해제
2. `LibreHardwareMonitor.exe`를 **관리자 권한으로 실행**
3. `Options → Remote Web Server → Run` 체크
4. 브라우저에서 `http://localhost:8085/data.json` 접속해 센서 데이터가 표시되는지 확인

### 설치 및 실행

1. 저장소 클론 후 `server/` 폴더로 이동

2. 가상환경(venv) 생성 및 활성화

```bash
   python -m venv venv
   venv\Scripts\activate
```

3. 의존 패키지 설치

```bash
   pip install -r requirements.txt
```

4. 서버 실행 (다른 기기에서도 접속할 수 있도록 `--host 0.0.0.0` 필수)

```bash
   uvicorn main:app --reload --host 0.0.0.0
```

5. 브라우저에서 `http://127.0.0.1:8000` 접속 확인

6. `agent/config.example.json`을 같은 폴더에 `config.json`으로 복사 후, 자신의 기기에 맞게 값 수정
- 다른 기기를 추가할 경우, 그 기기에서도 `agent/` 폴더와 자신만의 `config.json`을 두고 동일하게 실행

7. (별도 터미널) `agent/agent.py` 실행 → 대시보드에 CPU/GPU/RAM 값이 2초 간격으로 갱신되는지 확인

### 설정

`agent/config.json` (Git에 포함되지 않음, 각자 로컬에서 생성)

| 필드 | 설명 |
|---|---|
| `device_id` | 기기 고유 식별자 (예: `desktop`, `laptop`) |
| `device_name` | 대시보드에 표시될 이름 |
| `lhm_url` | LibreHardwareMonitor의 로컬 JSON 주소 |
| `server_url` | PulseGrid 서버 주소 (예: `http://<서버IP>:8000/api/v1/metrics`) |
| `sensor_map` | 기기별 SensorId 매핑 (CPU/GPU/RAM 등) |

`config.example.json`을 참고해 작성하며, 새 기기를 추가할 때는 `agent/config.example.json`을 복사해 그 기기에 맞는 값으로 채우면 됩니다.

---

## API 개요

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| `POST` | `/api/v1/metrics` | 수집기 → 서버 지표 전송 |
| `GET` | `/api/v1/devices` | 전체 기기 최신 상태 조회 |
| `GET` | `/api/v1/devices/{id}` | 특정 기기 상태 조회 |
| `GET` | `/api/v1/history` | 히스토리 조회 *(예정)* |
| `GET` | `/api/v1/health` | 서버 상태 확인 |
| `WS` | `/ws/dashboard` | 실시간 지표 수신 |

자세한 규격은 [API 명세서](docs/03_api_spec.md)를 참고하세요.

---

## 개발 로드맵

| 단계 | 내용 | 상태 |
|---|---|:---:|
| M0 | 환경 구성 | ✅ |
| M1 | 수집기 프로토타입 | ✅ |
| M2 | 서버 + 단일 기기 연동 | ✅ |
| M3 | 다중 기기 연동 | ✅ |
| M4 | 대시보드 완성 (**v1.0**) | ⬜ |
| M5 | 히스토리 저장 | ⬜ |
| M6 | 확장 지표 (디스크 / 배터리) | ⬜ |
| M7 | 문서화 및 정리 | ⬜ |

---

## 문서

| 문서 | 내용 |
|---|---|
| [요구사항 정의서](docs/01_requirements.md) | 기능 범위, 우선순위, 제약 조건 |
| [시스템 아키텍처](docs/02_architecture.md) | 전체 구조, 컴포넌트 역할, 기술 선택 근거 |
| [API 명세서](docs/03_api_spec.md) | 엔드포인트, 데이터 모델, WebSocket 규격 |
| [화면 설계서](docs/04_ui_design.md) | 레이아웃, 상태 표시 규칙, 반응형 대응 |
| [개발 일정](docs/05_milestones.md) | 마일스톤, 완료 기준, 리스크 관리 |
| [DEVLOG](docs/DEVLOG.md) | 세션별 작업 기록, 트러블슈팅 히스토리 |

---

## 개발 환경

<!-- TODO: 최종 확정 후 버전 명시 -->

| 항목 | 값 |
|---|---|
| Python | *(작성 예정)* |
| OS | Windows 11 |
| 테스트 기기 | 데스크탑(Ryzen 5 9600X / RTX 5070), 노트북(Core i7-1255U / Iris Xe) |

---

## 라이선스

<!-- TODO: 라이선스 결정 후 작성 -->

*(작성 예정)*
