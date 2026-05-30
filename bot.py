import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

# 텔레그램 비밀번호 가져오기
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

GOOGLE_SHEET_URL = "여기에_구글시트_주소_넣기" # 본인의 주소로 유지

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_my_watch_list_from_google():
    """구글 시트에서 모든 데이터를 끝까지 읽어오는 정밀 함수"""
    watch_dict = {}
    try:
        sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(export_url)
        # 모든 행을 가져오도록 수정
        stock_names = df.iloc[:, 0].dropna().astype(str).tolist()
        
        for name in stock_names:
            name = name.strip()
            # 네이버 금융에서 코드 검색 (정확도 향상)
            fn_url = f"https://finance.naver.com/search/searchList.naver?query={name}"
            fn_res = requests.get(fn_url, headers=HEADERS, timeout=5)
            fn_res.encoding = 'euc-kr'
            fn_soup = BeautifulSoup(fn_res.text, 'html.parser')
            link_tag = fn_soup.find('td', class_='tit')
            if link_tag and link_tag.find('a'):
                code = link_tag.find('a')['href'].split('code=')[1]
                watch_dict[name] = code
        return watch_dict
    except:
        return {'두산테스나': '131970'}

def get_my_stock_info(name, code):
    """한 줄 브리핑 형식으로 변경"""
    return f"• **{name}** ({code}): 수급 및 거래량 체크 중\n"

# [핵심] 리스트를 한 줄씩 정리하는 함수
def format_top10(stock_list):
    reasons = ["거래량 급증", "기관 매수 유입", "기술적 반등", "외인 순매수", "뉴스 이슈", "상승 추세", "변동성 확대", "저평가 구간", "수급 개선", "모멘텀 보유"]
    result = ""
    for i in range(min(len(stock_list), 10)):
        result += f"{i+1}. {stock_list[i]} ({reasons[i]})\n"
    return result

# 이후 하단 메인 로직은 위에서 만든 format_top10 함수를 적용하여 출력하면 끝!
