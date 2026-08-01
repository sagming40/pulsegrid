from pydantic import BaseModel
from typing import Optional


# BaseModel을 상속받으면 "나도 운송장 양식이야" 라고 선언하는 것
# 이제부터 CpuMetric은 usage, temp 두 칸이 있는 전용 양식지가 됨
class CpuMetric(BaseModel):
    usage: Optional[float] = None   # 소수(float)여야 하고, 없으면(Optional) None 허용
    temp: Optional[float] = None
    power: Optional[float] = None   # ⭐ M6.5 추가 — Watt 단위
    
class GpuMetric(BaseModel):
    usage: Optional[float] = None
    temp: Optional[float] = None    # 내장그래픽(Iris Xe)은 None 
    power: Optional[float] = None   # ⭐ M6.5 추가  

class RamMetric(BaseModel):
    usage: Optional[float] = None
    used_gb: Optional[float] = None
    total_gb: Optional[float] = None
    
class DiskMetric(BaseModel):
    id: str      # ⭐ Task 6-1(M6) 추가
    label: str   # ⭐ 추가 — 화면에 보여줄 이름표
    usage: Optional[float] = None
    temp: Optional[float] = None
    
class BatteryMetric(BaseModel):
    level: Optional[float] = None
    charging: Optional[bool] = None    # boolean = True/False
    
class MetricPayload(BaseModel):
    # 필수 항목 — 기본값(= None)을 주지 않으면 Pydantic이 "이게 없으면 받지 않음"으로 처리함
    device_id: str
    device_name: str
    timestamp: str
    cpu: CpuMetric
    ram: RamMetric
    
    # gpu는 0(필수)인데 값 자체는 null 가능 — "칸은 반드시 있어야 하지만, 그 안 내용물은 비어있어도 됨"
    gpu: Optional[GpuMetric] = None
    
    # disk, battery는 X(선택) — 아예 필드를 보내지 않아도 괜찮음
    disk: Optional[list[DiskMetric]] = None   # ⭐ Task 6-1(M6) 수정 — 상자 하나 → 상자 담는 리스트
    battery: Optional[BatteryMetric] = None                
