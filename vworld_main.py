import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from module.utility import Vworld_Api, LandSoil_Api
import plotly.express as px
import json


# V-world API 키 설정
VWORLD_API_KEY = "75DB4568-501C-34B3-BE40-CAF1FEE594B2"
PUBLIC_API_KEY = "1rTRcPcrgRX4bckCMPyIIgsMgxqzwZwAKsqCjJe74xrEwdc2rQRZgHAZ60aJdhT6313RnB8znsO2jJONz+ltow=="

vworld_api = Vworld_Api(VWORLD_API_KEY)

# 사용자에게 주소 입력받기
st.set_page_config(layout="wide",
                   page_title="토지 정보 및 토양 분석")
st.title("V-world 지도")
address = st.text_input("지번 주소를 입력하세요:")

# 기본 지도 HTML 파일 불러오기
with open("source/vworld_map.html", "r") as f:
    map_html = f.read()

if address:
    # 주소를 좌표로 변환
    lng, lat, pnu_code = vworld_api.get_coordinates_from_address(address)
    if lng and lat:
        # st.success(f"좌표: 경도 {lng}, 위도 {lat}")

        # 필지의 다각형 경계선 데이터 가져오기
        polygon_coords = vworld_api.get_land_polygon(lng, lat)  # 이 함수는 필지의 다각형 좌표 데이터를 반환

        # 좌표 데이터를 문자열로 변환하여 전달 (JSON 형식의 배열)
        polygon_coords_str = str(polygon_coords)

        # HTML에서 V-world API Key와 BBOX 좌표를 사용하도록 업데이트
        map_html = map_html.replace("{{ vworld_api_key }}", VWORLD_API_KEY)
        map_html = map_html.replace("{{ center_lng }}", str(lng))
        map_html = map_html.replace("{{ center_lat }}", str(lat))
        map_html = map_html.replace("{{ polygon_coords }}", polygon_coords_str)  # 2차원 배열로 전달

        price, use_area, land_area, land_use_info, land_height, terrain_shape, road_contact, nomination_name = vworld_api.get_land_info(pnu_code)
        land_info_df = pd.DataFrame({'공시지가': price,
                                     '용도지역': use_area,
                                     '토지면적': land_area,
                                     '토지이용상황': land_use_info,
                                     '지형높이': land_height,
                                     '지형형상': terrain_shape,
                                     '도로접면': road_contact,
                                     '지목명': nomination_name
                                     }, index=[0])

        soil_exam = LandSoil_Api(PUBLIC_API_KEY)
        soil_df = soil_exam.get_soil_exam(pnu_code)
        st.dataframe(land_info_df)

    else:
        st.error("해당 주소에 대한 좌표를 찾을 수 없습니다.")
        soil_df = pd.DataFrame({'No_data' : 'Nodata'}, index=[0])

else:
    # 기본 좌표 (서울)로 설정
    map_html = map_html.replace("{{ vworld_api_key }}", VWORLD_API_KEY)
    map_html = map_html.replace("{{ center_lng }}", "14134010.407660155")  # 서울의 경도
    map_html = map_html.replace("{{ center_lat }}", "4518887.569199997")   # 서울의 위도
    map_html = map_html.replace("{{ polygon_coords }}", "")
    soil_df = pd.DataFrame({'No_data' : 'Nodata'}, index=[0])

# HTML 컴포넌트로 지도 렌더링
components.html(map_html, height=600)
st.dataframe(soil_df)
if "No_data" in soil_df.columns:
    st.write("토양 성분 그래프 없음")
else:
    col_num = len(soil_df.columns)
    cols = st.columns(col_num)
    target_df = soil_df.iloc[:,1:]

    # 적정 범위 정의
    optimal_ranges = {
        "산도(1:5)": (5.5, 6.5),
        "유효인산(mg/kg)": (80, 120),
        "유효규산(mg/kg)": (157, 180),
        "유기물(g/kg)": (25, 30),
        "마그네슘(cmol+/kg)": (1.5, 2.0),
        "칼륨(cmol+/kg)": (0.25, 0.3),
        "칼슘(cmol+/kg)": (5.0, 6.0),
        "전기전도도(dS/m)": (0, 2.0)

    }

    for i, col in enumerate(target_df.columns):
        with cols[i]:
            fig = px.bar(
                target_df,
                y=col,
                labels={"index": f"{col}"}
            )
            fig.update_yaxes(title=None, range=[0, max(target_df[col].max(), optimal_ranges[col][1]) * 1.1])

            # 적정 범위의 가로선 추가
            fig.add_shape(
                type="line",
                x0=-0.5,
                x1=0.5,
                y0=optimal_ranges[col][0],  # 적정 범위 하한
                y1=optimal_ranges[col][0],
                line=dict(color="black", width=2, dash="dash"),
                name="적정 하한"
            )
            fig.add_shape(
                type="line",
                x0=-0.5,
                x1=0.5,
                y0=optimal_ranges[col][1],  # 적정 범위 상한
                y1=optimal_ranges[col][1],
                line=dict(color="red", width=2, dash="dash"),
                name="적정 상한"
            )

            st.plotly_chart(fig, use_container_width=True)



