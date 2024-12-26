import streamlit as st
import streamlit.components.v1 as components
from jinja2 import Template
import requests
import json
from urllib.parse import quote

# Google Maps API 키 설정
GOOGLE_MAPS_API_KEY = "AIzaSyDilaX7vc_VUnLwEDhBSO1rCKy_wJQN58w"

# 기본 지도 중심 좌표 설정 (서울)
default_lat = 37.5665
default_lng = 126.9780


# Google Geocoding API를 사용하여 주소를 좌표로 변환
def get_coordinates_from_address_google(address):
    api_key = GOOGLE_MAPS_API_KEY
    encoded_address = quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if len(data['results']) > 0:
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            return None, None
    else:
        print("API 요청 실패, 상태 코드:", response.status_code)
        print("응답 내용:", response.text)
        return None, None


# Overpass API를 사용하여 좌표 기반으로 주소 경계선 데이터 가져오기
def get_boundary_data_from_coordinates(lat, lon):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    is_in({lat}, {lon})->.a;
    rel(pivot.a)[boundary=administrative];
    out geom;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})

    if response.status_code == 200:
        try:
            data = response.json()

            # 데이터 구조 확인
            if 'elements' in data and len(data['elements']) > 0:
                element = data['elements'][0]

                # Relation 내부에 있는 members에서 way 객체의 geometry 정보를 추출
                if 'members' in element:
                    coordinates = []
                    for member in element['members']:
                        if member['type'] == 'way' and 'geometry' in member:
                            # 여기서 lat, lng 순서로 변환하여 저장
                            way_coords = [(point['lat'], point['lon']) for point in member['geometry']]
                            coordinates.extend(way_coords)
                    return coordinates
                else:
                    print(f"'members' 키가 응답에 없습니다. 응답 데이터: {element}")
                    return None
            else:
                print("경계 데이터를 찾을 수 없습니다. 응답 데이터에 'elements'가 없습니다.")
                return None
        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            print("응답 내용:", response.text)  # 응답 내용을 출력하여 확인
            return None
    else:
        print("API 요청 실패, 상태 코드:", response.status_code)
        print("응답 내용:", response.text)
        return None


# 사용자로부터 주소 입력 받기
st.title("GIS 웹 애플리케이션 - 주소 경계선 폴리곤 표시")

address = st.text_input("주소를 입력하세요:", "")

# 지도 HTML 파일을 불러와서 렌더링
with open("google_maps.html", "r") as file:
    google_maps_html = file.read()

if address:
    # Google Geocoding API를 사용하여 주소의 좌표 가져오기
    lat, lon = get_coordinates_from_address_google(address)

    if lat and lon:
        # Overpass API를 통해 경계선 데이터 가져오기
        boundary_data = get_boundary_data_from_coordinates(lat, lon)

        if boundary_data:
            # 중심 좌표를 좌표로 설정
            center_lat = lat
            center_lng = lon

            # 경계선 좌표를 GeoJSON 형식으로 변환
            coordinates = boundary_data

            # HTML 파일 내의 템플릿 변수에 실제 값 삽입 (Jinja2 사용)
            template = Template(google_maps_html)
            rendered_html = template.render(
                api_key=GOOGLE_MAPS_API_KEY,
                center_lat=center_lat,
                center_lng=center_lng,
                polygon_coordinates=coordinates
            )

            # Streamlit에서 렌더링
            components.html(rendered_html, height=600)
        else:
            st.error("해당 주소의 경계 데이터를 찾을 수 없습니다.")
    else:
        st.error("입력한 주소의 좌표를 찾을 수 없습니다.")
else:
    # 기본적으로 지도를 서울 중심으로 렌더링
    template = Template(google_maps_html)
    rendered_html = template.render(
        api_key=GOOGLE_MAPS_API_KEY,
        center_lat=default_lat,
        center_lng=default_lng,
        polygon_coordinates=[]
    )

    # 지도 기본 표시
    components.html(rendered_html, height=600)
