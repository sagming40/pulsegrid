# PulseGrid — DEVLOG

> 세션별 개발 회고 및 트러블슈팅 기록

이 문서는 마일스톤 문서(`05_milestones.md`)처럼 "계획"을 담는 곳이 아니라, **실제로 각 세션에서 무슨 일이 있었는지**를 기록하는 곳이다. 막혔던 지점, 해결한 방법, 다음에 참고할 만한 실수 등을 가감 없이 남긴다.

---

## 작성 규칙

- 세션(하루 작업 단위) 종료 시 또는 마일스톤 완료 시 기록
- 최신 항목이 위로 오도록 역순 정렬
- 형식: 날짜 / 관련 마일스톤 / 한 일 / 막혔던 점 / 다음에 할 일

---

## 2026-07-28 — M0 완료, 기획 문서 작성, GitHub 초기 세팅

**관련 마일스톤**: M0 (환경 구성) → 기획 단계

**한 일**
- LibreHardwareMonitor 설치 (노트북 + 데스크탑)
  - 최신 버전은 `PawnIO` 드라이버를 요구함 (구버전 `WinRing0` 대체)
- Remote Web Server 활성화 후 `http://localhost:8085/data.json` 응답 확인
- 기획 문서 5종 + README + `.gitignore` 작성
  - `01_requirements.md`, `02_architecture.md`, `03_api_spec.md`, `04_ui_design.md`, `05_milestones.md`
- 로컬 Git 저장소 초기화 → 첫 커밋 → GitHub 원격 저장소(`sagming40/pulsegrid`) 연결 및 push 완료

**막혔던 점 / 트러블슈팅**
- 노트북 쪽 LibreHardwareMonitor에서 `data.json`이 안 뜨는 문제 발생
  - 원인: `Options → Remote Web Server → Run` 체크 안 되어 있었음 (데스크탑은 켜져 있었는데 노트북만 놓침)
  - 교훈: 여러 기기에 같은 설정을 반복할 때는 체크리스트로 비교하며 진행할 것

**다음에 할 일**
- M1 시작: LibreHardwareMonitor JSON에서 CPU/GPU/RAM 값만 추출하는 Python 수집기 프로토타입 작성

---

<!--
다음 세션부터 이 형식으로 위에 추가할 것:

## YYYY-MM-DD — 한 줄 요약

**관련 마일스톤**: M?

**한 일**
-

**막혔던 점 / 트러블슈팅**
-

**다음에 할 일**
-
-->
