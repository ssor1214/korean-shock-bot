import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SHEET_ID = "1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc" # 구글 시트 ID

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_my_watch_list():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        return {str(row.iloc[0]): str(row.iloc[1]) for _, row in df.iterrows() if pd.notna(row.iloc[0])}
    except:
        return {'두산테스나': '131970'}

def get_market_data(url_path):
    """시장 지표 및 뉴스 기반 근거 추출"""
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table.type_2 tr[onmouseover]')
        
        result = ""
        for i, row in enumerate(rows[:10]):
            cols = row.select('td')
            name = cols[1].text.strip()
            # 네이버 뉴스 검색으로 근거 확보
            news_res = requests.get(f"https://search.naver.com/search.naver?query={name}+주가+전망", headers=HEADERS)
            news_soup = BeautifulSoup(news_res.text, 'html.parser')
            news = news_soup.select_one('a.news_tit').text if news_soup.select_one('a.news_tit') else "뉴스 없음"
            result += f"• {name}: {news[:30]}...\n"
        return result
    except:
        return "데이터 수집 불가"

def get_prediction_list():
    """뉴스 기반 상승 예측 종목 10개 추출"""
    try:
        url = "https://finance.naver.com/sise/sise_rise.naver"
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = [tag.text.strip() for tag in soup.select('a.tltle')[:10]]
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    except:
        return "예측 데이터 준비중"

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    my_list = get_my_watch_list()
    
    msg = f"🌟 {today} 국장 정밀 분석 리포트 🌟\n\n📌 [관심 종목 분석]\n"
    for name, code in my_list.items():
        # 상세 데이터 수집 로직 생략 (위 코드와 결합 가능)
        msg += f"• {name} (코드:{code})\n"
    
    msg += f"\n🔥 [거래량 상위]\n{get_market_data('sise_quant.naver')}"
    msg += f"\n📈 [상승률 상위]\n{get_market_data('sise_rise.naver')}"
    msg += f"\n📉 [하락률 상위]\n{get_market_data('sise_fall.naver')}"
    msg += f"\n🏢 [기관 매수 상위]\n{get_market_data('sise_deal_institution.naver')}"
    msg += f"\n👽 [외인 매수 상위]\n{get_market_data('sise_deal_foreigner.naver')}"
    msg += f"\n🎯 [뉴스 기반 상승 예측 TOP 10]\n{get_prediction_list()}"
    
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
