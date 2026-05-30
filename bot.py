import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 텔레그램 비밀번호 가져오기
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 질문자님의 관심 종목 (종목명: 종목코드)
# 나중에 종목을 바꾸거나 늘리고 싶다면 이 부분을 규칙에 맞게 수정하시면 됩니다!
WATCH_LIST = {
    '두산테스나': '131970',
    '삼성E&A': '028050',
    '두산로보틱스': '454910'
}

def get_stock_info(name, code):
    try:
        # 1. 네이버 증권에서 가격 및 거래량 가져오기
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 거래량 추출
        volume_table = soup.find('table', class_='no_info')
        volume = volume_table.find_all('td')[2].find('span', class_='blind').text if volume_table else "데이터 없음"
        
        # 2. 투자자별 매매동향(외인/기관) 가져오기
        frgn_url = f"https://finance.naver.com/item/frgn.naver?code={code}"
        frgn_res = requests.get(frgn_url, headers=headers)
        frgn_soup = BeautifulSoup(frgn_res.text, 'html.parser')
        
        # 최근 날짜의 기관/외인 수급 추출
        rows = frgn_soup.find_all('tr', onmouseover="mouseOver(this)")
        if rows:
            target_row = rows[0].find_all('td')
            foreigner = target_row[6].text.strip() # 외인 순매수
            institution = target_row[5].text.strip() # 기관 순매수
        else:
            foreigner, institution = "0", "0"
            
        # 3. 최신 뉴스 10개 가져오기
        news_url = f"https://search.naver.com/search.naver?where=news&query={name}"
        news_res = requests.get(news_url, headers=headers)
        news_soup = BeautifulSoup(news_res.text, 'html.parser')
        news_titles = []
        for item in news_soup.select('.news_tit')[:10]:
            news_titles.append(f"• {item.text} ({item['href']})")
            
        news_str = "\n".join(news_titles) if news_titles else "최신 뉴스 없음"
        
        # 요약 보고서 작성
        report = f"📊 **[{name}] 분석 보고서**\n"
        report += f"• 전일 거래량: {volume}주\n"
        report += f"• 기관 수급: {institution} (단위: 주)\n"
        report += f"• 외인 수급: {foreigner} (단위: 주)\n"
        report += f"📰 **최신 주요 뉴스**\n{news_str}\n"
        return report
        
    except Exception as e:
        return f"❌ {name} 데이터 수집 중 오류 발생\n"

def send_telegram(message):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(telegram_url, json=payload)

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    final_message = f"🔔 {today} 국장 단타 관심종목 모니터링\n\n"
    
    for name, code in WATCH_LIST.items():
        final_message += get_stock_info(name, code) + "\n" + "—" * 15 + "\n\n"
        
    send_telegram(final_message)
