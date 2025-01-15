from urllib.request import Request, urlopen
from urllib.parse import urlencode
from pyproj import Transformer
import json
import xmltodict
import pandas as pd

class Vworld_Api:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_coordinates_from_address(self, address):

        url = "https://api.vworld.kr/req/address"
        queryParams = "?" + urlencode({
            "key": self.api_key,  # API 키 직접 사용
            "service": "address",
            "request": "getcoord",
            # "crs": "epsg:3857",
            "crs" : "epsg:4326",
            "address": address,
            "format": "json",
            "type": "parcel"})

        request = Request(url + queryParams)
        response = urlopen(request)
        if response.getcode() == 200:
            response_body = response.read()
            text_str = response_body.decode("utf-8")
            json_data = json.loads(text_str)
            if json_data['response']['status'] == 'OK':
                x = float(json_data['response']['result']['point']['x'])
                y = float(json_data['response']['result']['point']['y'])
                # ## 좌표 변환
                # transformer = Transformer.from_crs(4326, 3857)
                # x, y = transformer.transform(_lat, _lng)
                pnu_code = json_data['response']['refined']['structure']['level4LC']
                return x, y, pnu_code
            else:
                result = '주소의 좌표값을 찾을 수가 없습니다.'
                return result, None, None
        else:
            result = '주소의 좌표값을 찾을 수가 없습니다.'

            return result, None, None

    def get_land_polygon(self, x, y, dataset="LP_PA_CBND_BUBUN"):
        geoFilter = f"POINT({x} {y})"
        url = "https://api.vworld.kr/req/data"

        # API 요청 파라미터
        queryParams = "?" + urlencode({
            "key": self.api_key,  # API 키 직접 사용
            "service": "data",
            "request": "GetFeature",
            "data": dataset,
            "geomFilter": geoFilter,
            "format": "json",
            "geometry": "true",
            "attribute": "true",
            # "crs": "epsg:3857",
            "crs" : "epsg:4326",
            "domain": "www.v-world-test.com"
        })

        request = Request(url + queryParams)
        response = urlopen(request)
        if response.getcode() == 200:

            response_body = response.read()
            text_str = response_body.decode('utf-8')
            json_data = json.loads(text_str)

            _coordinates = json_data['response']['result']['featureCollection']['features'][0]['geometry']['coordinates'][0]
            coordinates = _coordinates[0]
            return coordinates

        else:
            coordinates = '주소의 폴리곤을 찾을 수가 없습니다.'
            return coordinates

    def get_land_info(self, pnu_code):
        url = "https://api.vworld.kr/ned/data/getLandCharacteristics"
        queryParams = "?" + urlencode({
            "key": self.api_key,  # API 키 직접 사용
            "pnu": pnu_code,
            "format": "json",
            "numOfRows": "100",
            "pageNo": "1",
            "domain": "www.v-world-test.com"
        })

        request = Request(url + queryParams)

        # GET 요청 (urlopen은 기본적으로 GET 메소드 사용)
        response_body = urlopen(request).read()
        text_str = response_body.decode('utf-8')
        json_data = json.loads(text_str)

        official_price = json_data['landCharacteristicss']['field'][0]['pblntfPclnd']
        use_area = json_data['landCharacteristicss']['field'][0]['prposArea1Nm']
        land_area = json_data['landCharacteristicss']['field'][0]['lndpclAr']
        land_use_info = json_data['landCharacteristicss']['field'][0]['ladUseSittnNm']
        land_height = json_data['landCharacteristicss']['field'][0]['tpgrphHgCodeNm']
        terrain_shape = json_data['landCharacteristicss']['field'][0]['tpgrphFrmCodeNm']
        road_contact = json_data['landCharacteristicss']['field'][0]['roadSideCodeNm']
        nomination_name = json_data['landCharacteristicss']['field'][0]['lndcgrCodeNm']

        return official_price, use_area, land_area, land_use_info, land_height, terrain_shape, road_contact, nomination_name

class LandSoil_Api:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_soil_exam(self, pnu_code):
        url = 'http://apis.data.go.kr/1390802/SoilEnviron/SoilExam/getSoilExam'
        queryParams = "?" + urlencode({
            'serviceKey': self.api_key,
            'PNU_Code': pnu_code
                                })

        request = Request(url + queryParams)
        response = urlopen(request)
        text_str = response.read().decode('utf-8')
        json_data = xmltodict.parse(text_str)


        try:
            exam_day = json_data['response']['body']['items']['item']['Exam_Day']
            acidity = float(json_data['response']['body']['items']['item']['ACID'])
            vldpha = float(json_data['response']['body']['items']['item']['VLDPHA'])
            vldsia = float(json_data['response']['body']['items']['item']['VLDSIA'])
            om = float(json_data['response']['body']['items']['item']['OM'])
            mg = float(json_data['response']['body']['items']['item']['POSIFERT_MG'])
            k = float(json_data['response']['body']['items']['item']['POSIFERT_K'])
            ca = float(json_data['response']['body']['items']['item']['POSIFERT_CA'])
            selc = float(json_data['response']['body']['items']['item']['SELC'])

            soil_df = pd.DataFrame({
                '토양검정일': exam_day,
                '산도(1:5)': acidity,
                '유효인산(mg/kg)': vldpha,
                '유효규산(mg/kg)': vldsia,
                '유기물(g/kg)': om,
                '마그네슘(cmol+/kg)': mg,
                '칼륨(cmol+/kg)': k,
                '칼슘(cmol+/kg)': ca,
                '전기전도도(dS/m)': selc
            }, index=[0])


        except KeyError:
            soil_df = pd.DataFrame({'No_data': '해당 필지의 토양 성분 분석 이력이 없습니다.'}, index=[0])

        return soil_df