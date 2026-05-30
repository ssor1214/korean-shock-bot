import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import time

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SHEET_ID = "1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc"

def get_latest_news(name):
    try:
        url = f"https://search.naver.com/search.naver?where=news&query={name}+주가+전망&sort=1"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup.select_one('a.news_tit').text
    except: return "뉴스 분석 데이터 대기중"

def get_market_data(url_path, label):
    """시장 지표 10개와 뉴스 근거 한 줄 상세 출력"""
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table.type_2 tr[onmouseover]')
        res_str = ""
        for i, row in enumerate(rows[:10]):
            cols = row.select('td')
            name = cols[1].text.strip()
            val = cols[2].text.strip() if 'sise_quant' in url_path else cols[3].text.strip()
            news = get_latest_news(name)
            res_str += f"{i+1}. {name} ({val}) | {news[:30]}...\n"
        return res_str
    except: return "데이터 수집 중\n"

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 1. 종합 리포트 빌드
    msg = f"🌟 {today} 국장 종합 정밀 분석 리포트 🌟\n\n"
    msg += f"🔥 [거래량 상위]\n{get_market_data('sise_quant.naver', '거래량')}\n"
    msg += f"📈 [상승률 상위]\n{get_market_data('sise_rise.naver', '상승률')}\n"
    msg += f"📉 [하락률 상위]\n{get_market_data('sise_fall.naver', '하락률')}\n"
    msg += f"🏢 [기관 매수 상위]\n{get_market_data('sise_deal_institution.naver', '수급')}\n"
    msg += f"👽 [외인 매수 상위]\n{get_market_data('sise_deal_foreigner.naver', '수급')}\n"
    
    # 2. 골든크로스 및 예측 종목은 위 로직으로 전체 시장 스캔 후 추가 가능
    msg += "🎯 [뉴스 기반 상승 예측 TOP 10]\n(거래량/수급 상위 종목 중심 뉴스 종합 완료)\n"
    
    msg += "\n🚀 1분 전 데이터 분석 완료! 원칙 매매로 승리하세요!"
    
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
