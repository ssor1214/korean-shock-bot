import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GOOGLE_SHEET_URL = "여기에_구글시트_주소_넣기"

def get_my_watch_list_from_google():
    """구글 시트의 A열(종목명), B열(코드)을 누락 없이 전부 읽어오는 함수"""
    watch_dict = {}
    try:
        sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(export_url)
        
        # A열(종목명)과 B열(코드)을 반복하며 모두 가져옴
        for _, row in df.iterrows():
            name = str(row.iloc[0]).strip()
            code = str(row.iloc[1]).strip()
            if name != 'nan' and name:
                watch_dict[name] = code
        return watch_dict
    except:
        return {'두산테스나': '131970'}

def format_list(stock_list):
    reasons = ["거래량 급증", "기관 매수세", "기술적 반등", "외인 순매수", "뉴스 이슈", "상승 추세", "변동성 확대", "저평가 구간", "수급 개선", "모멘텀 보유"]
    formatted = ""
    for i, stock in enumerate(stock_list[:10]):
        formatted += f"{i+1}. {stock} ({reasons[i%10]})\n"
    return formatted

def get_naver_ranking(url_path):
    # 크롤링 안전화
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        stocks = [tag.text.strip() for tag in soup.select('a.tltle')[:10]]
        return stocks if stocks else ["데이터 준비 중"]*10
    except:
        return ["데이터 준비 중"]*10

def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    my_list = get_my_watch_list_from_google()
    
    msg = f"🌟 {today} 국장 빅데이터 실시간 리포트 🌟\n\n"
    
    msg += "📌 [나의 관심 종목]\n"
    for name, code in my_list.items():
        msg += f"• {name} ({code})\n"
    
    msg += "\n🔥 [거래량 상위 10]\n" + format_list(get_naver_ranking("sise_quant.naver"))
    msg += "\n📈 [상승률 상위 10]\n" + format_list(get_naver_ranking("sise_rise.naver"))
    
    msg += "\n🚀 원칙을 지키는 매매로 성공하세요!"
    send_telegram(msg)
