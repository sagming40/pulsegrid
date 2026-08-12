# PulseGrid — API 명세서

> 수집기(Agent) ↔ 서버(Server) ↔ 대시보드(Web) 간 통신 규격 정의

- **작성일**: 2026-07-28
- **작성자**: 사공민규
- **버전**: v0.2
- **관련 문서**: 요구사항 정의서(01), 시스템 아키텍처(02)

---

## 1. 공통 규약

### 1.1 기본 정보

| 항목 | 값 |
|---|---|
| Base URL | `http://<서버IP>:8000` |
| API 버전 경로 | `/api/v1` |
| 데이터 형식 | JSON (`Content-Type: application/json`) |
| 문자 인코딩 | UTF-8 |
| 시간 형식 | ISO 8601 (`YYYY-MM-DDTHH:MM:SS`) |
| 시간대 | 로컬 시간 (KST) 기준 |

### 1.2 공통 응답 형식

**성공 시**
```json
{
  "success": true,
  "data": { }
}
```

**실패 시**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PAYLOAD",
    "message": "필수 필드 device_id가 누락되었습니다."
  }
}
```

### 1.3 공통 에러 코드

| HTTP 상태 | 에러 코드 | 설명 |
|---|---|---|
| 400 | `INVALID_PAYLOAD` | 요청 본문 형식 오류 또는 필수 필드 누락 |
| 404 | `DEVICE_NOT_FOUND` | 요청한 `device_id`에 해당하는 기기 없음 |
| 422 | `VALIDATION_ERROR` | 필드 타입/범위 오류 (FastAPI 기본 검증) |
| 500 | `INTERNAL_ERROR` | 서버 내부 오류 |

---

## 2. 데이터 모델

### 2.1 MetricPayload (수집기가 보내는 데이터)

| 필드 | 타입 | 필수 | 설명 |
|---|---|:---:|---|
| `device_id` | string | O | 기기 고유 식별자 (예: `desktop`, `laptop`) |
| `device_name` | string | O | 기기 표시 이름 (예: `DESKTOP-5VSB06S`) |
| `timestamp` | string | O | 수집 시각 (ISO 8601) |
| `cpu` | object | O | CPU 지표 |
| `gpu` | object \| null | O | GPU 지표 (없으면 `null`) |
| `ram` | object | O | 메모리 지표 |
| `disk` | array \| null | X | 디스크 지표 목록 (기기마다 개수 다름) |
| `battery` | object \| null | X | 배터리 지표 (노트북 한정) |

#### cpu 객체

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `usage` | float \| null | % | CPU 전체 사용률 (0.0 ~ 100.0) |
| `temp` | float \| null | °C | CPU 온도 |
| `power` | float \| null | W | CPU 소비 전력 (M6.5 추가) |

#### gpu 객체

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `usage` | float \| null | % | GPU 코어 사용률 |
| `temp` | float \| null | °C | GPU 코어 온도 (내장그래픽은 `null` 가능) |
| `power` | float \| null | W | GPU 소비 전력 (M6.5 추가, 내장그래픽도 값 제공됨) |

#### ram 객체

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `usage` | float \| null | % | 메모리 사용률 |
| `used_gb` | float \| null | GB | 사용 중인 용량 |
| `total_gb` | float \| null | GB | 전체 용량 |

#### disk 배열의 각 항목

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `id` | string | - | 디스크 식별자 (예: `main`, `sub`) |
| `label` | string | - | 화면에 표시할 사용자 지정 이름표 (예: `C: (SSD or HDD 1TB)`) |
| `usage` | float \| null | % | 디스크 사용 공간 비율 |
| `temp` | float \| null | °C | 디스크 온도 |

#### battery 객체

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `level` | float \| null | % | 잔량 |
| `charging` | boolean \| null | - | 충전 중 여부 |

### 2.2 null 처리 원칙

기기마다 보유한 센서가 다르므로, **없는 값은 필드 자체를 생략하지 않고 `null`로 채운다.**

- 데스크탑: `battery` → `null`
- 노트북(Iris Xe): `gpu.temp` → `null` (내장그래픽은 온도 센서 미제공)

> 이유: 프론트엔드가 항상 동일한 구조를 기대할 수 있어 분기 처리가 단순해진다.

---

## 3. REST API 엔드포인트

### 3.1 지표 전송 (Agent → Server)

```
POST /api/v1/metrics
```

**설명**: 각 기기의 수집기가 2초 간격으로 지표를 전송한다.

**Request Body**
```json
{
  "device_id": "desktop",
  "device_name": "DESKTOP-5VSB06S",
  "timestamp": "2026-07-28T23:15:00",
  "cpu": { "usage": 1.4, "temp": 46.0, "power": 6.8 },
  "gpu": { "usage": 0.0, "temp": 37.7, "power": 24.2 },
  "ram": { "usage": 32.0, "used_gb": 10.0, "total_gb": 32.0 },
  "disk": [
    { "id": "main", "label": "C: (SSD 1TB)", "usage": 44.1, "temp": 51.0 },
    { "id": "sub", "label": "D: (SSD 1TB)", "usage": 30.2, "temp": 42.0 }
  ],
  "battery": null
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "data": { "received_at": "2026-07-28T23:15:00" }
}
```

**동작**
1. 요청 본문 검증
2. 서버 메모리에 해당 `device_id`의 최신 상태 갱신
3. 연결된 모든 WebSocket 클라이언트에 브로드캐스트
4. 마지막 DB 저장 시각으로부터 1분 경과 시 DB에 기록

---

### 3.2 전체 기기 최신 상태 조회

> ⚠️ **미구현** — 기획 단계(v0.1)에서 설계했으나, `WS /ws/dashboard` 연결 시 `snapshot` 메시지가 이 역할을 대신하고 있어 별도 구현하지 않았다. REST 조회 후 WebSocket 연결하는 2단계 흐름 대신 WebSocket 하나로 초기 상태+실시간 갱신을 모두 처리하는 편이, "REST 응답 시점과 WS 연결 시점 사이 데이터 갱신을 놓칠 수 있는" 동기화 문제를 원천적으로 피할 수 있다고 판단했다. 아래 명세는 **설계 의도 기록용으로 남겨둔다.**

```
GET /api/v1/devices
```

**설명**: 대시보드 최초 로딩 시 현재 등록된 모든 기기의 최신 상태를 한 번에 조회한다. (WebSocket 연결 전 초기 화면 표시용)

**Response (200 OK)**
```json
{
  "success": true,
  "data": [
    {
      "device_id": "desktop",
      "device_name": "DESKTOP-5VSB06S",
      "timestamp": "2026-07-28T23:15:00",
      "status": "online",
      "cpu": { "usage": 1.4, "temp": 46.0, "power": 6.8 },
      "gpu": { "usage": 0.0, "temp": 37.7, "power": 24.2 },
      "ram": { "usage": 32.0, "used_gb": 10.0, "total_gb": 32.0 },
      "disk": [
        { "id": "main", "label": "C: (SSD 1TB)", "usage": 44.1, "temp": 51.0 },
        { "id": "sub", "label": "D: (SSD 1TB)", "usage": 30.2, "temp": 42.0 }
      ],
      "battery": null
    },
    {
      "device_id": "laptop",
      "device_name": "DESKTOP-9TR0GGV",
      "timestamp": "2026-07-28T23:14:58",
      "status": "online",
      "cpu": { "usage": 19.7, "temp": 67.0, "power": 28.2 },
      "gpu": { "usage": 1.1, "temp": null, "power": 3.5 },
      "ram": { "usage": 79.0, "used_gb": 12.3, "total_gb": 16.0 },
      "disk": [
        { "id": "main", "label": "C: (SSD 1TB)", "usage": 44.1, "temp": 51.0 },
        { "id": "sub", "label": "D: (SSD 1TB)", "usage": 30.2, "temp": 42.0 }
      ],
      "battery": { "level": 96.9, "charging": false }
    }
  ]
}
```

**status 필드**

| 값 | 조건 |
|---|---|
| `online` | 최근 10초 이내 데이터 수신 |
| `offline` | 10초 이상 데이터 미수신 |

---

### 3.3 특정 기기 최신 상태 조회

> ⚠️ **미구현** — 사유는 3.2와 동일.

```
GET /api/v1/devices/{device_id}
```

**Path Parameter**

| 이름 | 타입 | 설명 |
|---|---|---|
| `device_id` | string | 조회할 기기 식별자 |

**Response (200 OK)**: 3.2의 배열 요소와 동일한 단일 객체

**Response (404 Not Found)**
```json
{
  "success": false,
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "device_id 'tablet'에 해당하는 기기를 찾을 수 없습니다."
  }
}
```

---

### 3.4 히스토리 조회

```
GET /api/v1/history
```

**Query Parameters**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|:---:|---|---|
| `device_id` | string | O | - | 조회할 기기 |
| `minutes` | int | X | `60` | 지금부터 몇 분 전까지 조회할지 |

> 최초 설계는 `from`/`to`/`metric` 파라미터였으나, 구현 단계에서 "지금부터 N분 전까지"라는 상대적 범위가 프론트엔드 드롭다운(실시간/1시간/6시간/24시간) UX와 더 맞아떨어져 `minutes` 하나로 단순화했다.

**요청 예시**
```
GET /api/v1/history?device_id=desktop&minutes=60
```

**Response (200 OK)**

```json
{
  "success": true,
  "data": [
    {
      "recorded_at": "2026-08-01T22:00:00",
      "cpu_usage": 12.4,
      "cpu_temp": 48.0,
      "cpu_power": 6.8,
      "gpu_usage": 3.1,
      "gpu_temp": 39.2,
      "gpu_power": 24.2,
      "ram_usage": 55.0,
      "disk_usage": 44.1,
      "disk_temp": 51.0,
      "battery_level": null,
      "battery_charging": null
    }
  ]
}
```
> **설계 노트 — disk가 배열이 아니라 단일 값인 이유**: `MetricPayload`(실시간 전송용)의 `disk`는 여러 디스크를 담는 배열이지만, DB에 저장할 땐 `id="main"`인 디스크 하나만 대표로 골라 평탄화된 컬럼(`disk_usage`, `disk_temp`)에 저장한다. 히스토리 그래프가 기기당 하나의 추세선만 보여주면 충분해 다중 디스크를 그대로 저장할 필요가 없었기 때문. (`server/db.py`의 `save_metric_snapshot()` 참고)
>
> **참고**: `cpu_power`/`gpu_power`는 `device_metrics_history`에 저장은 되고 있었으나 `get_history()`의 `SELECT` 절에서 누락돼 있던 것을 M7 문서화 검수 과정에서 발견해 수정했다. (수정 전: 실시간 카드엔 전력이 표시되지만 히스토리 모드엔 반영되지 않는 상태)

**Response (400 Bad Request)** — `minutes`가 1 미만인 경우

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PAYLOAD",
    "message": "minutes는 1 이상이어야 합니다."
  }
}
```

---

### 3.5 시간대별 CPU 히트맵 조회
```
GET /api/v1/heatmap
```
**설명**: 최근 N시간 동안 쌓인 히스토리를 기기별·시간대(0~23시)별로 묶어 평균 CPU 사용률을 계산한다.

**Query Parameters**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|:---:|---|---|
| `hours` | int | X | `24` | 최근 몇 시간 데이터를 집계할지 |

**요청 예시**

```
GET /api/v1/heatmap?hours=24
```

**Response (200 OK)**


```json
{
  "success": true,
  "data": [
    { "device_id": "desktop", "hour_slot": 9, "avg_cpu_usage": 43.3, "sample_count": 12 },
    { "device_id": "desktop", "hour_slot": 10, "avg_cpu_usage": 51.7, "sample_count": 15 },
    { "device_id": "laptop", "hour_slot": 9, "avg_cpu_usage": 22.1, "sample_count": 12 }
  ]
}
```

> `hour_slot`은 `HOUR(recorded_at)` 기준(0~23)이며, **날짜 구분 없이 시간대만으로 묶는다.** 즉 "어제 9시"와 "오늘 9시" 데이터가 하나의 `hour_slot=9`로 합쳐진다. (`server/db.py`의 `get_heatmap()` 참고)

**Response (400 Bad Request)** — `hours`가 1 미만인 경우

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PAYLOAD",
    "message": "hours는 1 이상이어야 합니다."
  }
}
```

---

### 3.6 서버 상태 확인

> ⚠️ **미구현** — 외부 모니터링 도구 연동용으로 설계했으나, 1인 개인 프로젝트 특성상 아직 그런 외부 모니터링 자체가 없어 필요성이 생기지 않았다. M8(Flutter 모바일 클라이언트) 등에서 연결 확인 용도로 필요해지면 재검토 예정.

```
GET /api/v1/health
```

**설명**: 수집기가 서버 가용 여부를 확인하거나, 운영 중 헬스체크 용도로 사용.

**Response (200 OK)**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "connected_devices": 2,
    "websocket_clients": 1,
    "uptime_seconds": 3821
  }
}
```

---

## 4. WebSocket 명세

### 4.1 연결

```
WS /ws/dashboard
```

**설명**: 웹 대시보드가 서버에 연결하여 실시간 지표를 수신한다.

### 4.2 서버 → 클라이언트 메시지

모든 메시지는 `type` 필드로 종류를 구분한다.

#### (1) 초기 스냅샷 — `snapshot`

연결 직후 1회 전송. 현재 모든 기기의 최신 상태를 담는다.

```json
{
  "type": "snapshot",
  "data": [ /* GET /api/v1/devices 의 data 와 동일 */ ]
}
```

#### (2) 지표 갱신 — `metric_update`

수집기로부터 새 데이터를 받을 때마다 전송.

```json
{
  "type": "metric_update",
  "data": {
    "device_id": "laptop",
    "timestamp": "2026-07-28T23:15:02",
    "cpu": { "usage": 21.3, "temp": 68.0, "power": 24.5 },
    "gpu": { "usage": 1.4, "temp": null, "power": 3.2 },
    "ram": { "usage": 79.2, "used_gb": 12.4, "total_gb": 16.0 },
    "disk": [
      { "id": "main", "label": "C: (SSD 1TB)", "usage": 44.1, "temp": 51.0 },
      { "id": "sub", "label": "D: (SSD 1TB)", "usage": 30.2, "temp": 42.0 }
    ],
    "battery": { "level": 96.8, "charging": false }
  }
}
```

#### (3) 기기 상태 변경 — `device_status`

기기가 오프라인이 되거나 다시 온라인이 될 때 전송.

```json
{
  "type": "device_status",
  "data": {
    "device_id": "laptop",
    "status": "offline"
  }
}
```

### 4.3 클라이언트 → 서버 메시지

1차 릴리즈에서는 클라이언트가 서버로 보내는 메시지를 사용하지 않는다. (단방향 수신 전용)

> 2차 확장 시 특정 기기만 구독하는 `subscribe` 메시지 등을 추가할 수 있다.

---

## 5. 상태 코드 요약

| 엔드포인트 | 메서드 | 상태 | 성공 | 주요 실패 |
|---|---|---|---|---|
| `/api/v1/metrics` | POST | 구현됨 | 200 | 400, 422 |
| `/api/v1/devices` | GET | 미구현 | - | - |
| `/api/v1/devices/{id}` | GET | 미구현 | - | - |
| `/api/v1/history` | GET | 구현됨 | 200 | 400 |
| `/api/v1/heatmap` | GET | 구현됨 | 200 | 400 |
| `/api/v1/health` | GET | 미구현 | - | - |

---

## 6. 2차 확장 시 변경 예정 사항

| 항목 | 변경 내용 |
|---|---|
| 인증 | `POST /api/v1/metrics` 요청 시 `X-API-Key` 헤더 필수화 |
| 프로토콜 | HTTP → HTTPS, WS → WSS |
| 기기 등록 | 수집기 최초 실행 시 `POST /api/v1/devices/register` 로 사전 등록 |

---

## 7. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v0.1 | 2026-07-28 | 최초 작성 |
| v0.2 | 2026-08-12 | M6/M6.5 구현 현황 반영 — cpu/gpu에 power 필드 추가, history 파라미터를 from/to/metric → device_id/minutes로 변경(응답 구조도 함께 변경), heatmap 엔드포인트 신규 추가, devices/devices-id/health를 미구현으로 명시 |
