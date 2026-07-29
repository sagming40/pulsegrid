import time
from fastapi import FastAPI
from fastapi import WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
from models import MetricPayload

# ─────────────────────────────────────────────────────────────
# 순찰(백그라운드 작업) 관련 설정값
# ─────────────────────────────────────────────────────────────
OFFLINE_THRESHOLD_SECONDS = 10   # 이 시간(초) 넘게 연락이 없으면 offline 처리
PATROL_INTERVAL_SECONDS = 3      # 순찰을 도는 주기 (10초보다 짧아야 감지가 늦지 않음)


# ─────────────────────────────────────────────────────────────
# 서버가 켜질 때 순찰 알바생(백그라운드 작업)을 자동으로 채용하는 부분
# lifespan = "이 가게(서버)가 문 열 때부터 닫을 때까지" 를 관리하는 함수
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 켜지는 순간: 순찰 함수를 "백그라운드"에 등록 (여기서 실행하고 바로 다음 줄로)
    patrol_task = asyncio.create_task(patrol_offline_devices())
    yield   # 여기서부터 실제로 서버가 손님(요청)을 받기 시작함
    # 서버가 꺼지는 순간: 순찰 알배생도 같이 퇴근
    patrol_task.cancel()

# 매니저(app) 한 명 채용
# 이 app이 앞으로 모든 주소(엔드포인트)를 관리하게 됨
app = FastAPI(lifespan=lifespan)


# 지금 접속해있는 브라우저(WebSocket 연결)들을 담아두는 명단
# 비유: 라면집 홀 안에 지금 앉아있는 손님 목록 
connected_clients: list[WebSocket] = []

# 기기별 최신 데이터
latest_metrics: dict[str, MetricPayload] = {}

# ─────────────────────────────────────────────────────────────
# 새로 추가: 기기별 "마지막으로 연락 온 시각"과 "지금 online인지" 상태
# ─────────────────────────────────────────────────────────────
last_seen: dict[str, float] = {}     # {"desktop": 1782812345.2, "laptop": ...}
device_status: dict[str, str] = {}   # {"desktop": "online", "laptop": "offline"}

async def broadcast(message: dict):
    # 명단에 있는 모든 손님(연결된 브라우저)에게 같은 메시지를 전달
    for client in connected_clients:
        await client.send_json(message)


# "/" 라는 주소로 GET 요청이 오면 이 함수를 실행해서 응답하라는 뜻
# 비유: 가게 정문에 "누가 왔나요?" 라고 물어보면 "네, 저 왔습니다." 라고 대답하는 것
@app.get("/")
def read_root():
    return FileResponse("../web/index.html")


@app.post("/api/v1/metrics")
async def receive_metrics(payload: MetricPayload):
    # payload는 이미 Pydantic이 검수를 마친 "합격 택배"
    # 여기 도착했다는 것은 device_id, cpu, ram 등 필수 항목이 다 있다는 뜻
    latest_metrics[payload.device_id] = payload
    
    # ── 새로 추가되는 부분 ──
    # "이 기기, 방금 연락 왔다"를 서버의 시계 기준으로 기록
    # (agent 컴퓨터의 시계가 아니라, 서버가 실제로 받은 그 순간을 쓰는 것이 정확함)
    last_seen[payload.device_id] = time.time()
    
    # 이 기기 방금 전까지 offline 이었다가 지금 다시 살아난 거라면,
    # "다시 online 이다"라고 모두에게 알려야 함
    if device_status.get(payload.device_id) != "online":
        device_status[payload.device_id] = "online"
        await broadcast({
            "type": "device_status",
            "data": {"device_id": payload.device_id, "status": "online"}
        })
    # ── 여기까지 새로 추가 ──     
    
    # API 명세서(03) 4.2절 (2) metric_update 형식 그대로 브로드캐스트
    await broadcast({
        "type": "metric_update",
        "data": payload.model_dump()
    })
    
    return {
        "success": True,
        "data": {"received_at": payload.timestamp}
    }


# ─────────────────────────────────────────────────────────────
# 순찰 함수 (백그라운드 작업의 실제 내용물)
# ─────────────────────────────────────────────────────────────
async def patrol_offline_devices():
    """
    3초마다 한 번씩 깨어나서, 등록된 모든 기기를 순찰함.
    각 기기의 '마지막 연락 온 시각'을 확인해서,
    10초 넘게 반응이 없으면 offline으로 변경 후 방송함.
    """
    while True:
        await asyncio.sleep(PATROL_INTERVAL_SECONDS)   # 3초 쉬었다가 순찰 시작
        
        now = time.time()
        for device_id, seen_at in last_seen.items():
            # 지금까지 online이었는데, 마지막 연락으로 부터 10초가 넘었다면
            if device_status.get(device_id) == "online" and (now - seen_at) > OFFLINE_THRESHOLD_SECONDS:
                device_status[device_id] = "offline"
                await broadcast({
                    "type": "device_status",
                    "data": {"device_id": device_id, "status": "offline"}
                })


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()                  # "네, 연결 받았습니다" — 손님을 홀 안으로 들여보냄
    connected_clients.append(websocket)       # 손님 명단에 추가
    
    # 방금 들어온 이 손님(이 브라우저)한테만 현재 상황 브리핑
    # latest_metrics.values() = 창고(우편함)에 쌓여있는 기기별 최신 데이터 전부
    snapshot_data = []
    for device_id, metric in latest_metrics.items():
        dumped = metric.model_dump()
        dumped["status"] = device_status.get(device_id, "offline")  # 스냅샷에 실제 상태값도 같이 실어보냄
        snapshot_data.append(dumped)
    await websocket.send_json({
        "type": "snapshot",
        "data": snapshot_data
    })
    
    try:
        while True:
            # 클라이언트가 뭔가 보낼 때까지 여기서 "기다리는 척"먼 하고 있음
            # (1차 릴리즈는 클라이언트가 서버로 메시지를 보내지 않음. 연결 유지 목적)
            await websocket.receive_text()
    except Exception:
        # 브라우저가 창을 닫거나 연결이 끊기면 이 쪽으로 옴
        connected_clients.remove(websocket)   # 명단에서 제거 — 나간 손님 명단에서 지우기           
