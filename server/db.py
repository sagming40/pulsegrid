import json
import mariadb
from models import MetricPayload

# ── 설정 파일 불러오기 ──
# db_config.json = "창고 주소랑 출입 열쇠 적어둔 쪽지"
with open("db_config.json", "r", encoding="utf-8") as f:
    DB_CONFIG = json.load(f)
    
    
def get_connection():
    """
    DB 연결 함수
    비유: 창고에 전화를 걸어서 통화를 연결하는 것.
    호출할 때마다 새로 전화를 거는 방식(=매번 새 connection)으로 감.
    """
    return mariadb.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )
    
    
def save_metric_snapshot(device_id: str, payload: MetricPayload):
    """
    지금 이 순간의 지표 하나를 창고(device_metrics_history)에 한 줄로 저장.
    payload 안의 gpu/disk는 None일 수 있기 때문에 값이 존재할 때만 꺼냄.
    """
    #gpu, disk가 통째로 None인 경우를 대비하여 안전하게 값 꺼내기
    gpu_usage = payload.gpu.usage if payload.gpu else None         
    gpu_temp = payload.gpu.temp if payload.gpu else None         
    disk_usage = payload.disk.usage if payload.disk else None         
    disk_temp = payload.disk.temp if payload.disk else None
    
    conn = get_connection()
    cursor = conn.cursor()
    # %s 자리에 값을 안전하게 끼워넣는 방식 (SQL Injection 방지 ─ 문자열을 직법 이어붙이지 않음)
    cursor.execute(
        """
        INSERT INTO device_metrics_history
            (device_id, recorded_at, cpu_usage, cpu_temp, gpu_usage, gpu_temp, ram_usage, disk_usage, disk_temp)
        VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s)    
        """,
        (
            device_id,
            payload.cpu.usage,
            payload.cpu.temp,
            gpu_usage,
            gpu_temp,
            payload.ram.usage,
            disk_usage,
            disk_temp,
        ),
    )
    conn.commit()   # "진짜 창고에 넣어라"는 확정 도장
    cursor.close()
    conn.close()    # 연결 끊기 — 매번 연결을 닫아서 자원을 낭비하지 않음         
