import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SHEET_ID = "1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_latest_news(name):
    """네이버 뉴스에서 가장 최근(1분 전까지 포함) 기사 제목을 가져오는 함수"""
    try:
        url = f"https://search.naver.com/search.naver?where=news&query={name}&sm=tab_opt&sort=1" # 최신순 정렬
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        news_title = soup.select_one('a.news_tit').text
        return news_title
    except:
        return "관련 뉴스 수집 중"

def get_market_data_with_news(url_path):
    """데이터와 뉴스 근거를 함께 묶어주는 함수"""
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table.type_2 tr[onmouseover]')
        
        result = ""
        for row in rows[:10]:
            cols = row.select('td')
            name = cols[1].text.strip()
            val = cols[2].text.strip()
            news = get_latest_news(name) # 여기서 실시간 뉴스 근거 취합
            result += f"• {name} ({val}) | 근거: {news[:35]}...\n"
        return result
    except:
        return "데이터 준비중\n"

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 1. 관심종목 상세 분석
    msg = f"🌟 {today} 국장 정밀 분석 리포트 🌟\n\n📌 [관심 종목 9선]\n"
    # (관심종목 9개 상세 분석 부분도 get_latest_news를 활용하여 근거 추가 가능)
    
    # 2. 시장 데이터 및 뉴스 근거 취합
    msg += f"\n🔥 [거래량 상위 10]\n{get_market_data_with_news('sise_quant.naver')}"
    msg += f"\n📈 [상승률 상위 10]\n{get_market_data_with_news('sise_rise.naver')}"
    msg += f"\n📉 [하락률 상위 10]\n{get_market_data('sise_fall.naver')}"
    msg += f"\n🏢 [기관 매수 상위 10]\n{get_market_data_with_news('sise_deal_institution.naver')}"
    msg += f"\n👽 [외인 매수 상위 10]\n{get_market_data_with_news('sise_deal_foreigner.naver')}"
    
    msg += "\n🚀 실시간 뉴스 분석 완료! 원칙 매매로 승리하세요!"
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
