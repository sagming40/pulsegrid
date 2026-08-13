import json
import time
import asyncio
import requests
import xml.etree.ElementTree as ET

# ─────────────────────────────────────────────────────────────
# 설정파일(power_config.json)을 읽어오는 부분
# 비유: 사서(KPX)한테 가기 전에, "주소가 어디고 출입증이 어떤 건지" 적힌
#      메모지(config)를 먼저 꺼내 보는 것 
# ─────────────────────────────────────────────────────────────
with open("power_config.json", "r", encoding="utf-8") as f:
    _config = json.load(f)

SERVICE_KEY = _config["service_key"]
API_BASE_URL = _config["api_base_url"]
FETCH_INTERVAL_SECONDS = _config["fetch_interval_minutes"] * 60


# ─────────────────────────────────────────────────────────────
# 화이트보드(cache) ─ 이 곳에 최신 전력수급 정보를 적어두고, 
# 다른 사람이(end point)이 물어보면 KPX에 다시 가지 않고 이걸 보여줌
# ─────────────────────────────────────────────────────────────  
_power_cache: dict | None = None        # 아직 한 번도 받아오지 못했으면 None
_power_cache_updated_at: float | None = None


def _fetch_power_data_from_kpx() -> dict:
    """
    KPX(정확히는 apis.data.go.kr GateWay)에 실제로 전화를 걸어서
    오늘 하루치 전력수급 데이터를 받아온 뒤, 
    그 중 가장 최신(items 리스트의 맨 앞) 한 건만 골라서 돌려주는 함수.
    
    비유: 사서한테 "오늘 대출기록 전부 주세요" 라고 부탁한 다음,
         받은 두꺼운 장부에서 제일 최근 줄 하나만 손가락으로 짚는 것.
    """  
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 10,     # 어차피 맨 앞(최신) 1건만 사용하므로, 아예 1건만 요청
        "dataType": "xml",
    }
    
    response = requests.get(API_BASE_URL, params=params, timeout=10)
    response.raise_for_status()     # 상태코드가 200이 아니면 여기서 Error를 터뜨림
    
    # XML 문자열을 Python이 다룰 수 있는 "나무 구조"로 변환
    root = ET.fromstring(response.text)
    
    # 성공 여부 먼저 확인 (API 응답의 resultCode/errMsg 구조 재사용)
    result_code = root.findtext(".//resultCode")
    if result_code != "00":
        result_msg = root.findtext(".//resultMsg", default="알 수 없는 오류")
        raise RuntimeError(f"KPX API 오류: {result_code} - {result_msg}")
    
    first_item = root.find(".//items/item")
    if first_item is None:
        raise RuntimeError("KPX 응답에 items가 비어있습니다.")
    
    # XML의 각 Tag(문자열)를 사용하기 편한 dict + 숫자 타입으로 변환
    return {
        "base_datetime": first_item.findtext("baseDatetime"),
        "supply_ability": float(first_item.findtext("suppAbility")),
        "current_load": float(first_item.findtext("currPwrTot")),
        "forecast_load": float(first_item.findtext("forecastLoad")),
        "supply_reserve_power": float(first_item.findtext("suppReservePwr")),
        "supply_reserve_rate": float(first_item.findtext("suppReserveRate")),
        "operating_reserve_power": float(first_item.findtext("operReservePwr")),
        "operating_reserve_rate": float(first_item.findtext("operReserveRate")),
    }
    
    
async def update_power_cache_periodically():
    """
    fetch_interval_minutes(기본 15분)마다 한 번씩 깨어나서
    KPX로부터 최신 전력수급 data를 받아와 화이트보드(_power_cache)에 덮어씀
    
    save_history_periodically와 완전히 같은 뼈대 — "일정 시간마다 깨어나서, 무언가를 해온다"는 패턴.
    """    
    global _power_cache, _power_cache_updated_at
    
    while True:
        try:
            _power_cache = _fetch_power_data_from_kpx()
            _power_cache_updated_at = time.time()
            print(f"[power] 캐시 갱신 성공: {_power_cache['base_datetime']}")
        except Exception as e:
            # KPX가 잠깐 장애나 점검 중이어도 서버 전체가 다운되면 안되므로 여기서 잡아냄
            print(f"[power] 캐시 갱신 실패: {e}")
        
        await asyncio.sleep(FETCH_INTERVAL_SECONDS)
        
        
def get_power_cache() -> dict:
    """
    EndPoint(main.py)가 화이트보드 내용을 그냥 읽기만 할때 사용하는 함수
    KPX에 다시 요청을 하지 않고, 저장된 값을 돌려줌
    """                
    if _power_cache is None:
        return {
            "available": False,
            "message": "아직 전력수급 데이터를 한 번도 받아오지 못했습니다.",
        }
    
    return {
        "available": True,
        "updated_at": _power_cache_updated_at,
        **_power_cache,
    }    
