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
    cpu_power = payload.cpu.power
    gpu_power = payload.gpu.power if payload.gpu else None
    
    # 여러 디스크 중 "main" 이름표가 붙은 대표 하나만 골라낸다
    # 비유: 택배 상자들 중 "main"이라고 적힌 상자만 창고 기록에 남김
    primary_disk = None
    if payload.disk:
        for d in payload.disk:
            if d.id =="main":
                primary_disk = d
                break
        else:
            # break 없이 for문이 끝까지 다 돌았다 = "main" 이름표를 찾지 못했다.
            # 이런 경우에는 첫 번째 상자를 대표로 삼는다 (안전장치)
            primary_disk = payload.disk[0]    
             
    disk_usage = primary_disk.usage if primary_disk else None         
    disk_temp = primary_disk.temp if primary_disk else None
    
    battery_level = payload.battery.level if payload.battery else None
    battery_charging = payload.battery.charging if payload.battery else None
    
    conn = get_connection()
    cursor = conn.cursor()
    # %s 자리에 값을 안전하게 끼워넣는 방식 (SQL Injection 방지 ─ 문자열을 직법 이어붙이지 않음)
    cursor.execute(
        """
        INSERT INTO device_metrics_history
            (device_id, recorded_at, 
             cpu_usage, cpu_temp, cpu_power, 
             gpu_usage, gpu_temp, gpu_power, ram_usage, 
             disk_usage, disk_temp, 
             battery_level, battery_charging)
        VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)    
        """,
        (
            device_id,
            payload.cpu.usage,
            payload.cpu.temp,
            cpu_power,
            gpu_usage,
            gpu_temp,
            gpu_power,
            payload.ram.usage,
            disk_usage,
            disk_temp,
            battery_level,
            battery_charging,
        ),
    )
    conn.commit()   # "진짜 창고에 넣어라"는 확정 도장
    cursor.close()
    conn.close()    # 연결 끊기 — 매번 연결을 닫아서 자원을 낭비하지 않음         


def get_history(device_id: str, minutes: int = 60) -> list[dict]:
    """
    지정한 기기(device_id)의, 지금부터 `minutes`분 전까지의 기록을
    오래된 순서(시간순)로 꺼내옴.
    
    비유: 창고지기한테 "3번 선반, 지난 0분치 물건 모두 꺼내주시는데
    오래된 것부터 순서대로 주세요"라고 요청하는 것.
    """
    conn = get_connection()
    # dictionary=True → 결과를 (1, 'desktop', ...) Tuple이 아니라
    # {"id": 1, "device_id": "desktop", ...} Dictionary로 받음
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        """
        SELECT recorded_at, cpu_usage, cpu_temp, cpu_power,
               gpu_usage, gpu_temp, gpu_power, ram_usage,
               disk_usage, disk_temp, battery_level, battery_charging
        FROM device_metrics_history
        WHERE device_id = %s
          AND recorded_at >= NOW() - INTERVAL %s MINUTE
        ORDER BY recorded_at ASC         
        """,
        (device_id, minutes),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # recorded_at은 파이썬 datetime 객체로 넘어오는데,
    # JSON으로 내보낼 때는 문자열이어야 하므로 ISO 형식 문자열로 변환
    for row in rows:
        row["recorded_at"] = row["recorded_at"].isoformat()
    
    return rows    


def get_heatmap(hours: int = 24) -> list[dict]:
    """
    지금까지 쌓인 모든 히스토리 기록을 "몇 시에 들어왔는지"만 확인 후,
    기기별 24개 우체통(시간대)에 나눠 담아 각 우체통의 평균 CPU 사용률을 계산하여 돌려줌.
    
    비유: 날짜는 신경쓰지 않고 "9시에 온 택배들끼리, 3시에 온 택배들끼리"
    묶어서 각 묶음의 평균 무게를 재는 것.
    
    hours 파라미터는 "최근 며칠간 데이터만 볼지" 범위를 제한하는 용도.
    (기본값 24 = 최근 24시간 안에 쌓인 기록만 집계)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        """
        SELECT
            device_id,
            HOUR(recorded_at) AS hour_slot,
            AVG(cpu_usage) AS avg_cpu_usage,
            COUNT(*) AS sample_count
        FROM device_metrics_history
        WHERE recorded_at >= NOW() - INTERVAL %s HOUR
        GROUP BY device_id, HOUR(recorded_at)
        ORDER BY device_id, hour_slot    
        """,
        (hours,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # AVG()는 소숫점이 길게 출력될 수 있어서 가독성 편의를 고려하여 반올림
    # (예: 43.333333333 → 43.3)
    for row in rows:
        row["avg_cpu_usage"] = round(float(row["avg_cpu_usage"]), 1)
        
    return rows    
