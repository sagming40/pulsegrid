// ──────────────────────────────────────────────────────────────────
// 게시판(카드)들을 담아두는 창고
// key = device_id, value = 그 기기의 카드를 가리키는 HTML 요소 (카드 DOM)
// 이렇게 저장해두면, 매번 새로 안 만들고 "이미 있으면 재사용"이 가능함
// ──────────────────────────────────────────────────────────────────
const deviceCards = {};

// 값이 없으면(null/undefined) 대시(—)로 표시
// 이유: 04_ui_design 3.3절 — 행이 사라졌다 나타나면 카드가 출렁여서 화면이 흔들림
function formatUsage(value) {
    if (value === null || value === undefined) return "—";
    return `${value.toFixed(1)}%`;
}
function formatTemp(value) {
    if (value === null || value === undefined) return "—";
    return `${Math.round(value)}°C`;
}

function getOrCreateCard(deviceId, deviceName) {
    // 이미 이 기기의 게시판(카드)이 있으면 그걸 그대로 반환(재사용)
    if (deviceCards[deviceId]) {
        return deviceCards[deviceId];
    }

    // 아이콘 = 택배 상자 겉면 스티커. device_id에 "laptop"이 들어있으면 노트북 아이콘
    const icon = deviceId.includes("laptop") ? "💻" : "🖥️";

    // 없으면 새로 생성하여 화면에 붙임
    const card = document.createElement("div");
    card.className = "device-card";
    card.innerHTML = `
                <div class="card-header">
                    <span class="device-icon">${icon}</span>
                    <div class="device-title">
                        <div class="device-name">${deviceId}</div>
                        <div class="device-hostname">${deviceName ?? "—"}</div>
                    </div>
                    <span class="status-badge online">online</span>
                </div>
                
                <div class="metric-row" data-metric="cpu">
                    <div class="metric-label">
                        <span>CPU</span>
                        <span class="metric-usage">—</span>
                        <span class="metric-temp">· —</span>
                    </div>
                    <div class="gauge-track"><div class="gauge-fill"></div></div>
                </div>
                
                <div class="metric-row" data-metric="gpu">
                    <div class="metric-label">
                        <span>GPU</span>
                        <span class="metric-usage">—</span>
                        <span class="metric-temp">· —</span>
                    </div>
                    <div class="gauge-track"><div class="gauge-fill"></div></div>
                </div>
                
                <div class="metric-row" data-metric="ram">
                    <div class="metric-label">
                        <span>RAM</span>
                        <span class="metric-usage">—</span>
                    </div>
                    <div class="gauge-track"><div class="gauge-fill"></div></div>
                </div>
                
                <div class="card-footer">
                    <span class="disk-summary">디스크 —</span>
                    <span class="battery-summary">배터리 —</span>
                </div>    
            `;
    document.getElementById("cards-container").appendChild(card);
    deviceCards[deviceId] = card;
    addDeviceOption(deviceId);   // ⭐ Task 5-4-b(M5) 추가  
    return card;
}

// 사용률(%) 값을 넣으면 "정상/주의/위험" 중 어떤 상태인지 판정하는 함수
// 비유: 체온계 — 숫자를 보고 "체온이 정상/미열/고열 중 어떤 상태인지" 구분하는 역할
function usageLevel(value) {
    if (value === null || value === undefined) return "normal";
    if (value >= 90) return "danger";
    if (value >= 75) return "warning";
    return "normal";
}

// 온도(C) 값을 넣으면 "정상/주의/위험" 판정
function tempLevel(value) {
    if (value === null || value === undefined) return "normal";
    if (value >= 85) return "danger";
    if (value >= 70) return "warning";
    return "normal";
}

// 지표 행 하나(CPU/GPU/RAM)를 갱신하는 공용 함수
// → 택배 상자 하나를 열어서 "사용률"과 "온도" 라벨을 붙이고, 게이지 바 길이를 조절하는 역할
function updateMetricRow(card, metricName, usage, temp) {
    const row = card.querySelector(`.metric-row[data-metric="${metricName}"]`);
    row.querySelector(".metric-usage").innerText = formatUsage(usage);

    const tempEl = row.querySelector(".metric-temp");
    if (tempEl) {
        tempEl.innerText = `· ${formatTemp(temp)}`;
        // 기존에 붙어있던 level 클래스를 다 떼고, 지금 온도에 맞는 클래스만 다시 붙임
        tempEl.classList.remove("level-warning", "level-danger");
        const tLevel = tempLevel(temp);
        if (tLevel !== "normal") {
            tempEl.classList.add(`level-${tLevel}`);
        }
    }

    const fill = row.querySelector(".gauge-fill");
    fill.style.width = `${usage ?? 0}%`;
    // 게이지 바 — 기존 색깔 클래스를 떼고 새로 판정한 색 클래스를 붙임
    fill.classList.remove("level-normal", "level-warning", "level-danger");
    fill.classList.add(`level-${usageLevel(usage)}`);
}

function updateCardMetrics(deviceId, metric) {
    const card = getOrCreateCard(deviceId, metric.device_name);

    updateMetricRow(card, "cpu", metric.cpu.usage, metric.cpu.temp);
    maybePushChartPoint(deviceId, metric.cpu.usage);   // ⭐ 추가
    updateMetricRow(card, "gpu", metric.gpu.usage, metric.gpu.temp);
    updateMetricRow(card, "ram", metric.ram.usage, null);  // RAM 행엔 온도 표시 칸이 없어 null로 넘겨도 안전함

    const diskEl = card.querySelector(".disk-summary");
    diskEl.innerText = `디스크 ${formatUsage(metric.disk?.usage)}`;

    const batteryEl = card.querySelector(".battery-summary");
    if (metric.battery) {
        batteryEl.innerText = `배터리 ${Math.round(metric.battery.level)}%`;
        batteryEl.classList.remove("dim");
    } else {
        // 기기에 배터리가 아예 없는 경우 (예: 데스크탑) — 흐린 색으로 대시 표시
        batteryEl.innerText = "배터리 —";
        batteryEl.classList.add("dim");
    }
}

function updateCardStatus(deviceId, status) {
    const card = getOrCreateCard(deviceId);
    const badge = card.querySelector(".status-badge");
    badge.innerText = status;
    badge.className = `status-badge ${status}`;   // online 또는 offline 클래스
    card.classList.toggle("offline", status === "offline");
}

// ─────────────────────────────────────────────
// Chart.js 추이 그래프 (05_ui_design 5장 스펙)
// ─────────────────────────────────────────────
const MAX_POINTS = 30;       // 최근 30포인트만 유지 (2초 × 30 = 60초)
const CHART_TICK_INTERVAL_MS = 1800;  // 이 시간 안에 여러 기기가 몰려와도 기록은 한 번만

const chartColors = {};      // device_id → 선 색깔 저장
const colorPalette = ["#3a86ff", "#f4b400", "#8e44ad", "#e63946"];
const lastKnownUsage = {};   // device_id → 가장 최근에 들은 CPU 사용률 (이어 그리기용)
let lastChartTickAt = 0;     // 마지막으로 그래프에 기록계가 찍은 시각
let trendChart = null;

// 기기별로 고정된 선 색깔을 배정 (처음 등장한 순서대로 팔레트에서 하나씩 배정)
function getDeviceColor(deviceId) {
    if (!chartColors[deviceId]) {
        const idx = Object.keys(chartColors).length % colorPalette.length;
        chartColors[deviceId] = colorPalette[idx];
    }
    return chartColors[deviceId];
}

function initChart() {
    const ctx = document.getElementById("trend-chart").getContext("2d");
    trendChart = new Chart(ctx, {
        type: "line",
        data: { labels: [], datasets: [] },
        options: {
            animation: false,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 100, ticks: { callback: (v) => v + "%" } }
            },
            plugins: { legend: { position: "top" } }
        }
    });
}

// 이 기기 전용 선(dataset)이 아직 없으면 새로 만들고, 있으면 그걸 반환
function getOrCreateDataset(deviceId) {
    let dataset = trendChart.data.datasets.find((d) => d.deviceId === deviceId);
    if (!dataset) {
        dataset = {
            deviceId,
            label: deviceId,
            data: [],
            borderColor: getDeviceColor(deviceId),
            backgroundColor: getDeviceColor(deviceId),
            tension: 0.3,
            pointRadius: 0
        };
        trendChart.data.datasets.push(dataset);
    }
    return dataset;
}

// 기록계 역할 — 누가 소식을 보내든, 최소 1.8초 이상이 지나야만 새 점을 찍음
function maybePushChartPoint(deviceId, cpuUsage) {
    lastKnownUsage[deviceId] = cpuUsage;   // 값은 일단 항상 최신으로 저장해둠
    if (viewMode === "history") return;    // ⭐ Task 5-4-b(M5) 추가: history 보는 중엔 실시간 갱신

    const now = Date.now();
    if (now - lastChartTickAt < CHART_TICK_INTERVAL_MS) return;  // 너무 최근에 찍었으면 이번엔 건너뜀
    lastChartTickAt = now;

    const label = new Date().toLocaleTimeString("ko-KR", { hour12: false });
    trendChart.data.labels.push(label);
    if (trendChart.data.labels.length > MAX_POINTS) {
        trendChart.data.labels.shift();
    }

    // 지금까지 한 번이라도 소식이 왔던 모든 기기에 대해, 이번 틱의 값을 채워넣음
    Object.keys(lastKnownUsage).forEach((id) => {
        const dataset = getOrCreateDataset(id);
        dataset.data.push(lastKnownUsage[id]);
        if (dataset.data.length > MAX_POINTS) {
            dataset.data.shift();
        }
    });

    trendChart.update("none");   // "none" = 매번 애니메이션 없이 즉시 갱신
}

initChart();

// ───────────────────────────────────────────────
// WebSocket 연결 + 자동 재연결 (04_ui_design 4.4절)
// ───────────────────────────────────────────────
const RECONNECT_DELAY_MS = 3000;    // 끊기면 3초 후 다시 걸기
let ws = null;

function setConnectionStatus(connected) {
    const el = document.getElementById("connection-status");
    if (connected) {
        el.innerText = "● 실시간 연결";
        el.style.background = "#4caf50";
    } else {
        el.innerText = "● 연결 끊김";
        el.style.background = "#e63946";
    }
}

// "전화 걸기" 자체를 함수로 만들어둠 — 끊기면 이 함수를 다시 호출해서 재연결함
function connectWebSocket() {
    // window.location.hostname = 지금 이 페이지에 접속한 주소를 그대로 재사용
    // (데스크탑에서 열었으면 127.0.0.1, 노트북에서 열었으면 192.168.219.105로 자동 대응)
    ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/dashboard`);

    ws.onopen = () => {
        setConnectionStatus(true);
    };

    // 서버에서 어떤 메시지가 올 때마다 이 코드가 실행됨
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);   // 문자열로 온 메시지를 다시 객체로 변환

        if (message.type === "snapshot") {
            // 연결 직후 한 번, 지금까지 서버가 알고 있던 모든 기기 정보를 한꺼번에 반영
            message.data.forEach((metric) => {
                updateCardMetrics(metric.device_id, metric);
                updateCardStatus(metric.device_id, metric.status);
            });
        }

        if (message.type === "metric_update") {
            updateCardMetrics(message.data.device_id, message.data);
        }

        if (message.type === "device_status") {
            updateCardStatus(message.data.device_id, message.data.status);
        }
    };

    // 연결이 끊기면(서버 재시작, 네트워크 문제 등) 여기로 옴
    ws.onclose = () => {
        setConnectionStatus(false);
        // 3초 후에 connectionWebSocket 자기 자신을 다시 호출 — 전화 다시 걸기
        setTimeout(connectWebSocket, RECONNECT_DELAY_MS);
    };
}

connectWebSocket();   // 페이지 로딩 시 첫 연결 시작

// ─────────────────────────
// 히스토리 조회 (Task 5-4-b)
// ─────────────────────────
let viewMode = "live"   // "live"(CCTV 모드) 또는 "history"(녹화 재생 모드)

const deviceSelectEl = document.getElementById("history-device-select");
const rangeSelectEl = document.getElementById("history-range-select");

// 드롭다운에 기기 목록을 채워넣는 함수. 이미 등록된 기기면 중복 추가 X
function addDeviceOption(deviceId) {
    const alreadyExists = [...deviceSelectEl.options].some((opt) => opt.value === deviceId);
    if (alreadyExists) return;

    const option = document.createElement("option");
    option.value = deviceId;
    option.innerText = deviceId;
    deviceSelectEl.appendChild(option);
} 

// 창고지기(API)한테 전화를 걸어서 "이 기기, 최근 0분치 주세요" 라고 요청 후 그래프에 그림
async function loadHistoryChart(deviceId, minutes) {
    const res = await fetch(`/api/v1/history?device_id=${deviceId}&minutes=${minutes}`);
    const result = await res.json();

    if (!result.success) {
        alert(`히스토리 조회 실패: ${result.error?.message ?? "알 수 없는 오류"}`);
        return;
    }

    const rows = result.data;

    // 실시간 그래프를 통째로 "재생 화면"으로 갈아 끼움
    trendChart.data.labels = rows.map((row) =>
        new Date(row.recorded_at).toLocaleTimeString("ko-KR", { hour12: false })
    );
    trendChart.data.datasets = [{
        deviceId,
        label: `${deviceId} (과거 기록)`,
        data: rows.map((row) => row.cpu_usage),
        borderColor: getDeviceColor(deviceId),
        backgroundColor: getDeviceColor(deviceId),
        tension: 0.3,
        pointRadius: 0
    }];
    trendChart.update();
}

// 드롭다운 중 하나라도 바뀌게 되면 이 함수가 실행됨
function applyViewMode() {
    const range = rangeSelectEl.value;

    if (range === "live") {
        viewMode = "live";
        deviceSelectEl.disabled = true;   // ⭐ Task 5-4-b(M5) 추가(수정) : 기기 드롭다운 비활성화
        // CCTV 모드로 복귀 — 화면 비우고, 다음 실시간 신호부터 다시 채워짐
        trendChart.data.labels = [];
        trendChart.data.datasets = [];
        trendChart.update();
        return;
    }
    viewMode = "history";
    deviceSelectEl.disabled = false;   // ⭐ Task 5-4-b(M5) 추가(수정) : 히스토리 모드에선 다시 활성화
    const deviceId = deviceSelectEl.value;
    if (!deviceId) return;   // 아직 연결된 기기가 하나도 없으면 아무것도 하지 않음

    loadHistoryChart(deviceId, Number(range));
}

deviceSelectEl.addEventListener("change", applyViewMode);
rangeSelectEl.addEventListener("change", applyViewMode);
