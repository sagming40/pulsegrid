# PulseGrid — API 명세서

> 수집기(Agent) ↔ 서버(Server) ↔ 대시보드(Web) 간 통신 규격 정의

- **작성일**: 2026-07-28
- **작성자**: 사공민규
- **버전**: v0.1 (초안)
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
| `disk` | array \| null | X | 디스크 지표 목록 (P1, 기기마다 개수 다름) |
| `battery` | object \| null | X | 배터리 지표 (P1, 노트북 한정) |

#### cpu 객체

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `usage` | float \| null | % | CPU 전체 사용률 (0.0 ~ 100.0) |
| `temp` | float \| null | °C | CPU 온도 |

#### gpu 객체

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `usage` | float \| null | % | GPU 코어 사용률 |
| `temp` | float \| null | °C | GPU 코어 온도 (내장그래픽은 `null` 가능) |

#### ram 객체

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `usage` | float \| null | % | 메모리 사용률 |
| `used_gb` | float \| null | GB | 사용 중인 용량 |
| `total_gb` | float \| null | GB | 전체 용량 |

#### disk 배열의 각 항목 (P1)

| 필드 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `id` | string | - | 디스크 식별자 (예: `main`, `sub`) |
| `usage` | float \| null | % | 디스크 사용 공간 비율 |
| `temp` | float \| null | °C | 디스크 온도 |

#### battery 객체 (P1)

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
  "cpu": { "usage": 1.4, "temp": 46.0 },
  "gpu": { "usage": 0.0, "temp": 37.7 },
  "ram": { "usage": 32.0, "used_gb": 10.0, "total_gb": 32.0 },
  "disk": [
      { "id": "main", "usage": 44.1, "temp": 51.0 },
      { "id": "sub", "usage": 30.2, "temp": 42.0 }
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
4. (P1) 마지막 DB 저장 시각으로부터 1분 경과 시 DB에 기록

---

### 3.2 전체 기기 최신 상태 조회

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
      "cpu": { "usage": 1.4, "temp": 46.0 },
      "gpu": { "usage": 0.0, "temp": 37.7 },
      "ram": { "usage": 32.0, "used_gb": 10.0, "total_gb": 32.0 },
      "disk": [
        { "id": "main", "usage": 44.1, "temp": 51.0 },
        { "id": "sub", "usage": 30.2, "temp": 42.0 }
      ],
      "battery": null
    },
    {
      "device_id": "laptop",
      "device_name": "DESKTOP-9TR0GGV",
      "timestamp": "2026-07-28T23:14:58",
      "status": "online",
      "cpu": { "usage": 19.7, "temp": 67.0 },
      "gpu": { "usage": 1.1, "temp": null },
      "ram": { "usage": 79.0, "used_gb": 12.3, "total_gb": 16.0 },
      "disk": [
        { "id": "main", "usage": 44.1, "temp": 51.0 },
        { "id": "sub", "usage": 30.2, "temp": 42.0 }
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

### 3.4 히스토리 조회 (P1)

```
GET /api/v1/history
```

**Query Parameters**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|:---:|---|---|
| `device_id` | string | O | - | 조회할 기기 |
| `from` | string | X | 1시간 전 | 시작 시각 (ISO 8601) |
| `to` | string | X | 현재 | 종료 시각 (ISO 8601) |
| `metric` | string | X | `all` | 조회 지표 (`cpu`, `gpu`, `ram`, `all`) |

**요청 예시**
```
GET /api/v1/history?device_id=desktop&from=2026-07-28T22:00:00&metric=cpu
```

**Response (200 OK)**
```json
{
  "success": true,
  "data": {
    "device_id": "desktop",
    "metric": "cpu",
    "points": [
      { "timestamp": "2026-07-28T22:00:00", "usage": 12.4, "temp": 48.0 },
      { "timestamp": "2026-07-28T22:01:00", "usage": 8.1,  "temp": 46.5 }
    ]
  }
}
```

---

### 3.5 서버 상태 확인

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
    "cpu": { "usage": 21.3, "temp": 68.0 },
    "gpu": { "usage": 1.4, "temp": null },
    "ram": { "usage": 79.2, "used_gb": 12.4, "total_gb": 16.0 },
    "disk": [
      { "id": "main", "usage": 44.1, "temp": 51.0 },
      { "id": "sub", "usage": 30.2, "temp": 42.0 }
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

| 엔드포인트 | 메서드 | 성공 | 주요 실패 |
|---|---|---|---|
| `/api/v1/metrics` | POST | 200 | 400, 422 |
| `/api/v1/devices` | GET | 200 | 500 |
| `/api/v1/devices/{id}` | GET | 200 | 404 |
| `/api/v1/history` | GET | 200 | 400, 404 |
| `/api/v1/health` | GET | 200 | - |

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
