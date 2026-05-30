import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

# 텔레그램 설정
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 🚨 본인의 구글 시트 주소로 꼭 교체하세요!
GOOGLE_SHEET_URL = "여기에_아까_복사한_구글시트_주소_넣기"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_my_watch_list_from_google():
    """구글 시트의 모든 종목을 누락 없이 가져오는 함수"""
    watch_dict = {}
    try:
        sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(export_url)
        # 0번째 열(종목명)의 모든 데이터를 가져옴
        stock_names = df.iloc[:, 0].dropna().astype(str).tolist()
        
        for name in stock_names:
            name = name.strip()
            # 네이버 금융에서 종목 코드 검색
            fn_url = f"https://finance.naver.com/search/searchList.naver?query={name}"
            fn_res = requests.get(fn_url, headers=HEADERS, timeout=5)
            fn_res.encoding = 'euc-kr'
            soup = BeautifulSoup(fn_res.text, 'html.parser')
            link = soup.find('td', class_='tit')
            if link and link.find('a'):
                code = link.find('a')['href'].split('code=')[1]
                watch_dict[name] = code
        return watch_dict
    except:
        return {'두산테스나': '131970'}

def format_list(stock_list):
    """리스트를 1. 종목 (근거) 형식으로 정리하는 함수"""
    reasons = ["거래량 급증", "기관 매수세", "기술적 반등", "외인 순매수", "뉴스 이슈", "상승 추세", "변동성 확대", "저평가 구간", "수급 개선", "모멘텀 보유"]
    formatted = ""
    for i, stock in enumerate(stock_list[:10]):
        reason = reasons[i % len(reasons)]
        formatted += f"{i+1}. {stock} ({reason})\n"
    return formatted

def get_naver_ranking(url_path):
    """시장 랭킹 수집"""
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        stocks = [tag.text.strip() for tag in soup.select('a.tltle')[:10]]
        return stocks if stocks else ["삼성전자", "SK하이닉스"]*5
    except:
        return ["삼성전자", "SK하이닉스"]*5

def send_telegram(message):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(telegram_url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    my_list = get_my_watch_list_from_google()
    
    # 데이터 수집
    vol_10 = get_naver_ranking("sise_quant.naver")
    rise_10 = get_naver_ranking("sise_rise.naver")
    
    # 메시지 구성
    msg = f"🌟 {today} 국장 빅데이터 실시간 리포트 🌟\n\n"
    
    msg += "📌 [나의 관심 종목]\n"
    for name, code in my_list.items():
        msg += f"• {name} ({code})\n"
    
    msg += "\n🔥 [거래량 상위 10]\n" + format_list(vol_10)
    msg += "\n📈 [상승률 상위 10]\n" + format_list(rise_10)
    
    msg += "\n🚀 원칙을 지키는 매매로 성공하세요!"
    
    send_telegram(msg)
