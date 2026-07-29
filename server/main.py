from fastapi import FastAPI
from fastapi import WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models import MetricPayload

# 매니저(app) 한 명 채용
# 이 app이 앞으로 모든 주소(엔드포인트)를 관리하게 됨
app = FastAPI()


# 지금 접속해있는 브라우저(WebSocket 연결)들을 담아두는 명단
# 비유: 라면집 홀 안에 지금 앉아있는 손님 목록 
connected_clients: list[WebSocket] = []
latest_metrics: dict[str, MetricPayload] = {}


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
    
    # API 명세서(03) 4.2절 (2) metric_update 형식 그대로 브로드캐스트
    await broadcast({
        "type": "metric_update",
        "data": payload.model_dump()
    })
    
    return {
        "success": True,
        "data": {"received_at": payload.timestamp}
    }


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()                  # "네, 연결 받았습니다" — 손님을 홀 안으로 들여보냄
    connected_clients.append(websocket)       # 손님 명단에 추가
    
    # 방금 들어온 이 손님(이 브라우저)한테만 현재 상황 브리핑
    # latest_metrics.values() = 창고(우편함)에 쌓여있는 기기별 최신 데이터 전부
    snapshot_data = [metric.model_dump() for metric in latest_metrics.values()]
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
