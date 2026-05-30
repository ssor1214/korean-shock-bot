import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 🚨 주소 복사 시 'https://docs.google.com/spreadsheets/d/' 와 '/edit' 사이의 문자열만 넣으세요!
SHEET_ID = "1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc" 

def get_my_watch_list():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        # 1행을 헤더로 인식, A열(0)과 B열(1)을 딕셔너리로 만듦
        return {str(row.iloc[0]): str(row.iloc[1]) for _, row in df.iterrows() if pd.notna(row.iloc[0])}
    except Exception as e:
        return {'에러': str(e)}

def get_market_data(url_path):
    """최근 데이터를 가져오되, 휴장일이면 지난 금요일 데이터를 가져오도록 네이버 금융 경로 보완"""
    try:
        # 네이버 금융 메인 페이지를 통해 마지막 거래일 데이터 확보
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 테이블의 tr 중 onmouseover가 있는 행들만 추출
        rows = soup.select('table.type_2 tr[onmouseover]')
        
        result = ""
        for i, row in enumerate(rows[:10]):
            cols = row.select('td')
            if len(cols) > 3:
                name = cols[1].text.strip()
                val = cols[2].text.strip()
                result += f"• {name}: {val}\n"
        return result if result else "데이터 없음"
    except:
        return "수집 실패"

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    my_list = get_my_watch_list()
    
    msg = f"🌟 {today} 국장 빅데이터 리포트 🌟\n\n📌 [관심 종목 총 {len(my_list)}개]\n"
    for name, code in my_list.items():
        msg += f"• {name} ({code})\n"
    
    msg += f"\n🔥 [거래량 상위]\n{get_market_data('sise_quant.naver')}"
    msg += f"\n📈 [상승률 상위]\n{get_market_data('sise_rise.naver')}"
    msg += f"\n📉 [하락률 상위]\n{get_market_data('sise_fall.naver')}"
    msg += f"\n🏢 [기관 매수 상위]\n{get_market_data('sise_deal_institution.naver')}"
    msg += f"\n👽 [외인 매수 상위]\n{get_market_data('sise_deal_foreigner.naver')}"
    
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
