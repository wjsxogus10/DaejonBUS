import requests
import xml.etree.ElementTree as ET
import time
import json

# ==========================================
# 👇 본인의 키를 넣어주세요 (따옴표 안에!)
# ==========================================
kakao_key = "949989b1747758ede537aac1af1d60db"
data_key  = "d37ef28959d3391d0285eb9bf3e2b1b438f495ff248bbe61ace7f32f290bed83"

# 추적할 주요 노선
target_routes = [
    {"id": "30300040", "name": "102번 (수통골-대전역)"},
    {"id": "30300037", "name": "105번 (충대-비래동)"},
    {"id": "30300038", "name": "106번 (비래동-목원대)"},
    {"id": "30300001", "name": "급행1번 (원내동-대전역)"},
    {"id": "30300002", "name": "급행2번 (봉산동-옥계동)"}
]

url = "http://openapitraffic.daejeon.go.kr/api/rest/busposinfo/getBusPosByRtid"

print("🛡️ [강철 관제 모드] 버스가 없어도 지도는 뜨게 합니다...")

while True:
    # 1. 변수 초기화
    all_bus_data = {}
    total_bus_count = 0
    status_msg = "데이터 수집 중..."
    current_time = time.strftime("%H:%M:%S")

    # 2. 데이터 수집 시도
    try:
        for route in target_routes:
            all_bus_data[route['name']] = [] # 빈 리스트 초기화
            
            params = {'serviceKey': data_key, 'busRouteId': route['id']}
            res = requests.get(url, params=params, timeout=5)
            
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                items = root.findall(".//itemList")
                
                route_buses = []
                for bus in items:
                    route_buses.append({
                        "no": bus.find("PLATE_NO").text,
                        "lat": bus.find("GPS_LATI").text,
                        "lng": bus.find("GPS_LONG").text
                    })
                
                all_bus_data[route['name']] = route_buses
                total_bus_count += len(route_buses)
                print(f"   ㄴ {route['name']}: {len(route_buses)}대")
            else:
                print(f"   ㄴ {route['name']}: 응답 없음")

        if total_bus_count == 0:
            status_msg = "현재 운행 중인 버스가 없습니다."
        else:
            status_msg = f"총 {total_bus_count}대 운행 중"

    except Exception as e:
        print(f"⚠️ 데이터 수집 에러: {e}")
        status_msg = "서버 연결 불안정 (지도는 표시됨)"

    # 3. HTML 생성 (무조건 실행)
    json_data = json.dumps(all_bus_data, ensure_ascii=False)
    
    options_html = ""
    for route in target_routes:
        options_html += f'<option value="{route["name"]}">{route["name"]}</option>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="10">
        <title>대전 버스 강철 지도</title>
        <style>
            body, html {{ margin:0; padding:0; width:100%; height:100%; }}
            #map {{ width:100%; height:100%; }}
            .panel {{
                position: absolute; top: 10px; right: 10px; z-index: 999;
                background: rgba(255, 255, 255, 0.95); padding: 15px; 
                border-radius: 10px; border: 2px solid #333;
                width: 220px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            }}
        </style>
    </head>
    <body>
    <div class="panel">
        <b>🚍 노선 선택</b>
        <select id="routeSelect" onchange="changeRoute()" style="width:100%; padding:5px; margin-top:5px;">
            {options_html}
        </select>
        <hr>
        <label><input type="checkbox" id="trafficChk" onclick="toggleTraffic()" checked> 🚦 교통정보 보기</label>
        <div style="font-size:12px; color:gray; margin-top:10px;">
            업데이트: {current_time}<br>
            <b>{status_msg}</b>
        </div>
    </div>

    <div id="map"></div>

    <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={kakao_key}"></script>
    <script>
        var container = document.getElementById('map');
        var options = {{ center: new kakao.maps.LatLng(36.3504, 127.3845), level: 8 }};
        var map = new kakao.maps.Map(container, options);
        
        map.addOverlayMapTypeId(kakao.maps.MapTypeId.TRAFFIC);

        var allBusData = {json_data};
        var currentMarkers = [];

        function toggleTraffic() {{
            var chk = document.getElementById("trafficChk");
            if (chk.checked) map.addOverlayMapTypeId(kakao.maps.MapTypeId.TRAFFIC);
            else map.removeOverlayMapTypeId(kakao.maps.MapTypeId.TRAFFIC);
        }}

        function changeRoute() {{
            var select = document.getElementById("routeSelect");
            var selectedRoute = select.value;
            localStorage.setItem("lastRoute", selectedRoute);

            for (var i = 0; i < currentMarkers.length; i++) currentMarkers[i].setMap(null);
            currentMarkers = [];

            var buses = allBusData[selectedRoute];
            if (!buses || buses.length === 0) return;

            for (var i = 0; i < buses.length; i++) {{
                var bus = buses[i];
                var marker = new kakao.maps.Marker({{
                    position: new kakao.maps.LatLng(bus.lat, bus.lng),
                    image: new kakao.maps.MarkerImage('https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/bus.png', new kakao.maps.Size(30, 32)),
                    title: bus.no
                }});
                marker.setMap(map);
                currentMarkers.push(marker);
                
                var iw = new kakao.maps.InfoWindow({{
                    content: '<div style="padding:5px; font-weight:bold;">' + selectedRoute + '<br>' + bus.no + '</div>'
                }});
                iw.open(map, marker);
            }}
        }}

        window.onload = function() {{
            var savedRoute = localStorage.getItem("lastRoute");
            if (savedRoute) document.getElementById("routeSelect").value = savedRoute;
            changeRoute();
        }};
    </script>
    </body>
    </html>
    """

    with open("real_bus_map.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"[{current_time}] 지도 갱신 완료 ({status_msg})")
    time.sleep(10)