import requests, os
from bs4 import BeautifulSoup
from datetime import datetime

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_market_data(url_path):
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table.type_2 tr[onmouseover]')
        
        result = ""
        for i, row in enumerate(rows[:10]):
            cols = row.select('td')
            name = cols[1].text.strip()
            # 종목별 뉴스 검색 (상세 근거 2줄 추출)
            news_url = f"https://search.naver.com/search.naver?where=news&query={name}+주가+분석"
            news_res = requests.get(news_url, headers={'User-Agent': 'Mozilla/5.0'})
            news_soup = BeautifulSoup(news_res.text, 'html.parser')
            news = news_soup.select_one('a.news_tit').text
            
            result += f"{i+1}. {name} | 뉴스: {news}\n"
        return result
    except: return "데이터 수집 실패\n"

if __name__ == "__main__":
    msg = "🔥 [시장 종합 정밀 리포트]\n\n"
    msg += f"거래량 상위:\n{get_market_data('sise_quant.naver')}\n"
    msg += f"상승률 상위:\n{get_market_data('sise_rise.naver')}\n"
    msg += f"하락률 상위:\n{get_market_data('sise_fall.naver')}\n"
    
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
