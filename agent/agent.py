import requests
import time

# LibreHardwareMonitor가 데이터를 차려놓는 "식탁" 주소
LHM_URL = "http://localhost:8085/data.json"

# ───────────────────────────────────────────────────────────────────────
# 센서 매핑 테이블
# "이름(Text)"이 겹치는 문제 때문에, 대신 SensorId(고유 주소)로 찾는다.
# 나중에(M3) 노트북용 매핑표가 따로 필요하면 이 딕셔너리를 device_id별로 분리할 예정.
# ───────────────────────────────────────────────────────────────────────
SENSOR_MAP = {
    "cpu_usage": "/amdcpu/0/load/0",             # CPU Total (전체 사용률)
    "cpu_temp": "/amdcpu/0/temperature/2",       # Core (Tctl/Tdie)
    "gpu_usage": "/gpu-nvidia/0/load/0",         # RTX 5070 GPU Core 사용률
    "gpu_temp": "/gpu-nvidia/0/temperature/0",   # RTX 5070 GPU Core 온도
    "ram_usage": "/ram/load/0",                  # 실제 물리 RAM 사용률 (가상메모리 아님)
    "ram_used": "/ram/data/0",                   # 사용중인 용량 (GB)
    "ram_available": "/ram/data/1",              # 남은 용량 (GB)
}


def find_by_sensor_id(node, target_id):
    """
    마트료시카 인형 열어보기 함수 (버전 2).
    이번엔 '이름표(Text)'가 아니라 '고유 주소(SensorId)'로 찾는다.
    이름은 겹칠 수 있지만 주소는 절대 겹치지 않으므로 훨씬 안전함.
    """
    # 1. 이 인형이 내가 찾는 그 주소를 가지고 있는지 확인
    if node.get("SensorId") == target_id:
        return node.get("Value")    # 발견 => 예: "48.5 °C" (아직 문자열 상태)
    
    # 2. 찾지 못했으면 더 작은 인형(Children)들 안을 계속 열어보며 찾는다.
    for child in node.get("Children", []):
        result = find_by_sensor_id(child, target_id)
        if result is not None:
            return result   # 어딘가에서 찾았다면 바로 반환, 더 열어보지 않음
        
    # 3. 끝까지 다 열어보았지만 없다면 아예 없는 것
    return None  


def parse_value(raw_value):
    """
    LibreHardwareMonitor는 값을 "48.5 °C", "15.9 %" 처럼
    숫자 + 단위가 붙은 '문자열'로 준다.
    이 중 숫자만 뽑아서 float(실수)fh 변환하는 역할
    
    비유: 택배 상자 안에 "사과 5개"라고 적혀있다면,
         숫자 '5'만 필요하고 '개'라는 단위는 불필요 한것과 같음.
    """
    if raw_value is None:
        return None
    try:
        # 공백 기준으로 잘라서 첫 번째 조각(숫자 부분)만 사용
        # 예: "48.5 °C" → ["48.5". "°C"] → "48.5" → 48.5
        number_part = raw_value.split()[0]
        return float(number_part)
    except (ValueError, IndexError):
        # 값이 "-" 처럼 숫자가 아닌 경우 등 예외 상황 대비
        return None
    
    
def collect_metrics(device_id, device_name):
    """
    창고(LibreHardwareMonitor)에서 필요한 값만 뽑아서
    API 명세서(03) 형식의 '택배 상자'로 포함하는 함수
    """            
    # 창고 문 두드리기 (HTTP 요청 = "안에 뭐가 있는지 보여줘")
    response = requests.get(LHM_URL)
    raw_data = response.json()  # 창고 안 물건 목로 전체 (Dictionary로 변환됨)
    
    # 매핑 테이블에 적힌 주소대로 하나씩 찾아서 숫자로 변환
    cpu_usage = parse_value(find_by_sensor_id(raw_data, SENSOR_MAP["cpu_usage"]))
    cpu_temp = parse_value(find_by_sensor_id(raw_data, SENSOR_MAP["cpu_temp"]))
    gpu_usage = parse_value(find_by_sensor_id(raw_data, SENSOR_MAP["gpu_usage"]))
    gpu_temp = parse_value(find_by_sensor_id(raw_data, SENSOR_MAP["gpu_temp"]))
    ram_usage = parse_value(find_by_sensor_id(raw_data, SENSOR_MAP["ram_usage"]))
    ram_used = parse_value(find_by_sensor_id(raw_data, SENSOR_MAP["ram_used"]))
    ram_available = parse_value(find_by_sensor_id(raw_data, SENSOR_MAP["ram_available"]))
    
    # 사용중 + 남은용량 ≈ 전체용량 (LHM이 total_gb를 따로 주지 않기 때문에 직접 계산)
    ram_total = None
    if ram_used is not None and ram_available is not None:
        ram_total = round(ram_used + ram_available, 1)
        
    # API 명세서(03) 2.1절 MetricPayload 형식으로 포장
    payload = {
        "device_id": device_id,
        "device_name": device_name,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cpu": {"usage": cpu_usage, "temp": cpu_temp},
        "gpu": {"usage": gpu_usage, "temp": gpu_temp},
        "ram": {"usage": ram_usage, "used_gb": ram_used, "total_gb": ram_total},
        "disk": None,      # P1 확장 예정 (M6)
        "battery": None,   # 데스크탑이라 항상 None
    }
    return payload         
        

if __name__ == "__main__":
    # 2초마다 반복해서 값을 뽑아 터미널에 출력
    # M1 완료 기준: 이 반복문이 계속 정상적인 값을 찍으면 통과!
    while True:
        metrics = collect_metrics("desktop", "DESKTOP-5VSB06S")
        print(metrics)
        time.sleep(2)    
