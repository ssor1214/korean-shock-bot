import os, requests, pandas as pd
from bs4 import BeautifulSoup

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SHEET_ID = "1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc" # 본인의 시트 ID로 수정

def get_my_watch_list():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        return {str(row.iloc[0]): str(row.iloc[1]) for _, row in df.iterrows() if pd.notna(row.iloc[0])}
    except:
        return {}

def get_detail(name, code):
    try:
        # 1. 상세 페이지에서 가격/거래량 추출
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        price = soup.select_one('p.no_today span.blind').text
        change = soup.select_one('p.no_ex span.blind').text
        
        # 2. 최신 뉴스 제목 추출 (근거)
        news_url = f"https://search.naver.com/search.naver?where=news&query={name}+주가&sort=1"
        news_res = requests.get(news_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        news_soup = BeautifulSoup(news_res.text, 'html.parser')
        news = news_soup.select_one('a.news_tit').text
        
        return f"현재가: {price}원 | 등락: {change}\n근거: {news}"
    except:
        return "상세 정보 수집 대기중"

if __name__ == "__main__":
    watch_list = get_my_watch_list()
    msg = "📌 [관심 종목 정밀 리포트]\n\n"
    
    for name, code in watch_list.items():
        info = get_detail(name, code)
        msg += f"• {name} ({code})\n{info}\n\n"
        
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
