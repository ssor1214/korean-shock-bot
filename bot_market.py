import requests, os
from bs4 import BeautifulSoup

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_detailed_market_data(url_path):
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
            # 네이버 뉴스 상세 검색
            news_url = f"https://search.naver.com/search.naver?where=news&query={name}+주가+상승+요인"
            news_res = requests.get(news_url, headers={'User-Agent': 'Mozilla/5.0'})
            news_soup = BeautifulSoup(news_res.text, 'html.parser')
            
            # 뉴스 제목과 요약 근거 추출
            tit = news_soup.select_one('a.news_tit').text
            desc = news_soup.select_one('div.dsc_txt_wrap').text.strip() if news_soup.select_one('div.dsc_txt_wrap') else "시장 주목 종목."
            
            result += f"{i+1}. {name}\n   - 근거: {tit}\n   - 요약: {desc[:60]}...\n\n"
        return result
    except: return "데이터 수집 실패\n"

if __name__ == "__main__":
    msg = "🔥 [시장 종합 정밀 분석 리포트]\n\n"
    msg += f"🔥 거래량 상위 10선:\n{get_detailed_market_data('sise_quant.naver')}\n"
    msg += f"📈 상승률 상위 10선:\n{get_detailed_market_data('sise_rise.naver')}\n"
    msg += f"📉 하락률 상위 10선:\n{get_detailed_market_data('sise_fall.naver')}\n"
    msg += f"🏢 기관 매수 상위 10선:\n{get_detailed_market_data('sise_deal_institution.naver')}\n"
    msg += f"👽 외인 매수 상위 10선:\n{get_detailed_market_data('sise_deal_foreigner.naver')}\n"
    
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
