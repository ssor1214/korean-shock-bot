import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc/edit?gid=0#gid=0"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_my_watch_list():
    """구글 시트 A열(종목), B열(코드)을 끝까지 읽어오는 가장 확실한 방법"""
    try:
        sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(export_url)
        # 종목명과 코드가 들어있는 A, B열만 추출
        return {str(row.iloc[0]): str(row.iloc[1]) for _, row in df.iterrows() if pd.notna(row.iloc[0])}
    except:
        return {'두산테스나': '131970'}

def get_market_data(url_path, label):
    """주말/휴일에도 데이터가 나오도록 마지막 장 마감 데이터 활용"""
    try:
        # 네이버 금융의 시세 페이지 접속
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 테이블의 모든 tr을 가져와서 데이터 확인
        rows = soup.select('table.type_2 tr[onmouseover="mouseOver(this)"]')
        
        result = ""
        count = 0
        for row in rows:
            if count >= 10: break
            cols = row.select('td')
            if len(cols) > 3:
                name = cols[1].text.strip()
                val = cols[2].text.strip() # 가격/거래량
                result += f"• {name}: {val}\n"
                count += 1
        return result if result else "시장 휴장/데이터 갱신 대기\n"
    except:
        return "데이터 불러오기 실패\n"

def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    my_list = get_my_watch_list()
    
    msg = f"🌟 {today} 국장 빅데이터 리포트 🌟\n\n📌 [관심 종목 {len(my_list)}개]\n"
    for name, code in my_list.items():
        msg += f"• {name} ({code})\n"
    
    # 8가지 섹션 구성
    msg += f"\n🔥 [거래량 상위]\n{get_market_data('sise_quant.naver', '거래량')}"
    msg += f"\n📈 [상승률 상위]\n{get_market_data('sise_rise.naver', '상승률')}"
    msg += f"\n📉 [하락률 상위]\n{get_market_data('sise_fall.naver', '하락률')}"
    msg += f"\n🏢 [기관 매수 상위]\n{get_market_data('sise_deal_institution.naver', '기관 매수')}"
    msg += f"\n👽 [외인 매수 상위]\n{get_market_data('sise_deal_foreigner.naver', '외인 매수')}"
    msg += f"\n🏦 [기관 매도 상위]\n{get_market_data('sise_deal_institution.naver?sosok=0&day=1', '기관 매도')}"
    msg += f"\n👿 [외인 매도 상위]\n{get_market_data('sise_deal_foreigner.naver?sosok=0&day=1', '외인 매도')}"
    
    msg += "\n🚀 원칙을 지키는 매매로 성공하세요!"
    send_telegram(msg)
