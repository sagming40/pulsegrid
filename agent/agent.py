import requests
import time
import json   # 스티커(config.json)를 읽으려면 json 모듈이 필요해

# ───────────────────────────────────────────────────────────────────
# 설정 파일 읽기
# config.json = 이 agent가 "누구 짐이고, 어디로 보낼지" 적힌 이름표 스티커
# 코드 안에 하드코딩하지 않고, 매번 이 파일을 열어서 확인만 함
# ───────────────────────────────────────────────────────────────────
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    
DEVICE_ID = config["device_id"]
DEVICE_NAME = config["device_name"]
LHM_URL = config["lhm_url"]
SERVER_URL = config["server_url"]
SENSOR_MAP = config["sensor_map"]     


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
    
    
def collect_metrics():
    """
    device_id, device_name은 이제 매개변수로 받지 않음.
    파일 맨 위에서 이미 config.json을 읽어 DEVICE_ID, DEVICE_NAME
    전역변수로 만들어놨으니, 함수 안에서 그 값을 가져다 씀.
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
        "device_id": DEVICE_ID,
        "device_name": DEVICE_NAME,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cpu": {"usage": cpu_usage, "temp": cpu_temp},
        "gpu": {"usage": gpu_usage, "temp": gpu_temp},
        "ram": {"usage": ram_usage, "used_gb": ram_used, "total_gb": ram_total},
        "disk": None,      # P1 확장 예정 (M6)
        "battery": None,   # 추후 노트북 config에서 battery 항목 추가 예정 (M6)
    }
    return payload         
        

if __name__ == "__main__":
    # 2초마다 반복해서 값을 뽑아 터미널에 출력
    # M1 완료 기준: 이 반복문이 계속 정상적인 값을 찍으면 통과!
    while True:
        metrics = collect_metrics()
        print(metrics)
        
        # 뽑은 값을 서버로 전송 (택배 상자를 서버 접수처로 보내는 것)
        try:
            response = requests.post(SERVER_URL, json=metrics)
            print("서버 응답:", response.json())
        except requests.exceptions.RequestException as e:
            # 서버가 꺼져 있거나 네트워크 문제가 생겼을 때
            print("서버 전송 실패:", e)    
        
        time.sleep(2)    
