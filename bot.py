import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GOOGLE_SHEET_URL = "여기에_본인의_구글시트_주소_넣기"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_my_watch_list():
    try:
        sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(export_url)
        # 빈 값 제거 후 모든 행 가져오기
        data = df.dropna(subset=[df.columns[0]])
        return {str(row.iloc[0]): str(row.iloc[1]) for _, row in data.iterrows()}
    except:
        return {'두산테스나': '131970'}

def get_naver_ranking(url_path, base_reason):
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        stocks = [tag.text.strip() for tag in soup.select('a.tltle')[:10]]
        
        # 10개 강제 보장
        while len(stocks) < 10: stocks.append("데이터 준비중")
        
        result = ""
        for i, s in enumerate(stocks):
            result += f"{i+1}. {s} ({base_reason} {i+1}위)\n"
        return result
    except:
        return "데이터 수집 실패\n"

def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    my_list = get_my_watch_list()
    
    msg = f"🌟 {today} 국장 빅데이터 리포트 🌟\n\n📌 [관심 종목]\n"
    for name, code in my_list.items():
        msg += f"• {name} ({code})\n"
    
    msg += f"\n🔥 [거래량 상위]\n{get_naver_ranking('sise_quant.naver', '거래량')}"
    msg += f"\n📈 [상승률 상위]\n{get_naver_ranking('sise_rise.naver', '상승률')}"
    msg += f"\n📉 [하락률 상위]\n{get_naver_ranking('sise_fall.naver', '하락률')}"
    msg += f"\n🏢 [기관 매수 상위]\n{get_naver_ranking('sise_deal_institution.naver', '기관 매수')}"
    msg += f"\n👽 [외인 매수 상위]\n{get_naver_ranking('sise_deal_foreigner.naver', '외인 매수')}"
    msg += f"\n🏦 [기관 매도 상위]\n{get_naver_ranking('sise_deal_institution.naver?sosok=0&day=1', '기관 매도')}"
    msg += f"\n👿 [외인 매도 상위]\n{get_naver_ranking('sise_deal_foreigner.naver?sosok=0&day=1', '외인 매도')}"
    msg += f"\n📰 [뉴스 이슈 상위]\n{get_naver_ranking('sise_group.naver?type=item', '뉴스 이슈')}"
    
    msg += "\n🚀 원칙을 지키는 매매로 성공하세요!"
    send_telegram(msg)
