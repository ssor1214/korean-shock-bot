import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc/edit?gid=0#gid=0"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_my_watch_list():
    """모든 행을 누락 없이 가져오기 위해 header=0을 사용하여 1행을 헤더로 처리"""
    try:
        sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(export_url)
        # 모든 행 순회
        return {str(row.iloc[0]): str(row.iloc[1]) for _, row in df.iterrows() if pd.notna(row.iloc[0])}
    except:
        return {'두산테스나': '131970'}

def get_detail_data(url_path, category):
    """실시간 시세 또는 수급 데이터를 정밀하게 긁어오는 함수"""
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 랭킹 테이블 찾기
        table = soup.select_one('table.type_2')
        rows = table.select('tr[onmouseover="mouseOver(this)"]')
        
        result = ""
        for i, row in enumerate(rows[:10]):
            cols = row.select('td')
            name = cols[1].text.strip()
            # 거래량/금액 또는 수급량 추출 (표 구조에 따라 인덱스 조정)
            val = cols[2].text.strip() if category != "수급" else cols[3].text.strip()
            result += f"{i+1}. {name} ({val})\n"
        return result if result else "데이터 준비중\n"
    except:
        return "장 마감/장중 데이터 갱신 대기중\n"

def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    my_list = get_my_watch_list()
    
    msg = f"🌟 {today} 국장 빅데이터 리포트 🌟\n\n📌 [관심 종목]\n"
    for name, code in my_list.items():
        msg += f"• {name} ({code})\n"
    
    # 카테고리별 URL 및 데이터 매핑
    msg += f"\n🔥 [거래량 상위]\n{get_detail_data('sise_quant.naver', '거래량')}"
    msg += f"\n📈 [상승률 상위]\n{get_detail_data('sise_rise.naver', '거래량')}"
    msg += f"\n📉 [하락률 상위]\n{get_detail_data('sise_fall.naver', '거래량')}"
    msg += f"\n🏢 [기관 매수 상위]\n{get_detail_data('sise_deal_institution.naver', '수급')}"
    msg += f"\n👽 [외인 매수 상위]\n{get_detail_data('sise_deal_foreigner.naver', '수급')}"
    
    msg += "\n🚀 원칙을 지키는 매매로 성공하세요!"
    send_telegram(msg)
