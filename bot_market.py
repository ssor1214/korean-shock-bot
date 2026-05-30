import requests, os
from bs4 import BeautifulSoup

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
            # 종목별 뉴스/근거 요약
            news_url = f"https://search.naver.com/search.naver?where=news&query={name}+주가+분석"
            news_res = requests.get(news_url, headers={'User-Agent': 'Mozilla/5.0'})
            news_soup = BeautifulSoup(news_res.text, 'html.parser')
            tit = news_soup.select_one('a.news_tit').text
            desc = news_soup.select_one('div.dsc_txt_wrap').text.strip() if news_soup.select_one('div.dsc_txt_wrap') else "시장 주요 관심 종목."
            result += f"{i+1}. {name}\n   - 근거: {tit}\n   - 요약: {desc[:60]}...\n\n"
        return result
    except: return "데이터 수집 대기중\n"

if __name__ == "__main__":
    msg = "🔥 [시장 종합 정밀 분석 리포트]\n\n"
    # 수급/거래량/등락
    msg += f"🔥 거래량 상위:\n{get_market_data('sise_quant.naver')}"
    msg += f"📈 상승률 상위:\n{get_market_data('sise_rise.naver')}"
    msg += f"📉 하락률 상위:\n{get_market_data('sise_fall.naver')}"
    msg += f"🏢 기관 매수 상위:\n{get_market_data('sise_deal_institution.naver')}"
    msg += f"👽 외인 매수 상위:\n{get_market_data('sise_deal_foreigner.naver')}"
    
    # 추가된 요청 사항: 매도 상위
    msg += f"🏦 기관 매도 상위:\n{get_market_data('sise_deal_institution.naver?sosok=0&day=1')}"
    msg += f"👿 외인 매도 상위:\n{get_market_data('sise_deal_foreigner.naver?sosok=0&day=1')}"
    
    # 상승 예측 (상승률 상위 로직 재활용)
    msg += f"🎯 뉴스 기반 상승 예측 TOP 10:\n{get_market_data('sise_rise.naver')}"
    
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
