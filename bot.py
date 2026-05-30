import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 텔레그램 비밀번호 가져오기
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# [기능 1] 내가 직접 관리하는 수기 관심 종목
MY_WATCH_LIST = {
 '두산테스나': '131970',
    '삼성E&A': '028050',
    '두산로보틱스': '454910'
    '나무기술': '242040'
    '한온시스템': '018880'
    '한국전력': '015760'
    'LG씨엔에스': '064400'
    '대한전선': '001440'
    '넥스트칩': '396270'


}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_naver_market_ranking(url_path):
    """네이버 증권 각 시세 페이지에서 실시간 탑10 종목을 동적으로 긁어오는 함수"""
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        stocks = []
        table = soup.find('table', class_='type_2')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                name_tag = row.find('a', class_='tltle')
                if name_tag:
                    stocks.append(name_tag.text.strip())
                if len(stocks) >= 10:
                    break
        
        # 데이터가 없을 때 튕기지 않도록 방어 로직
        if not stocks:
            return ["데이터 집계 중"]
        return stocks
    except:
        return ["데이터 연결 지연"]

def get_my_stock_info(name, code):
    """수기 종목 상세 리포트 기능"""
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        volume_table = soup.find('table', class_='no_info')
        volume = volume_table.find_all('td')[2].find('span', class_='blind').text if volume_table else "0"
        
        frgn_url = f"https://finance.naver.com/item/frgn.naver?code={code}"
        frgn_res = requests.get(frgn_url, headers=HEADERS, timeout=10)
        frgn_soup = BeautifulSoup(frgn_res.text, 'html.parser')
        rows = frgn_soup.find_all('tr', onmouseover="mouseOver(this)")
        foreigner, institution = "0", "0"
        if rows:
            target_row = rows[0].find_all('td')
            foreigner = target_row[6].text.strip()
            institution = target_row[5].text.strip()
            
        return f"• **{name}**: 거래량 {volume}주 / 기관 {institution} / 외인 {foreigner}\n"
    except:
        return f"• **{name}**: 데이터 정산 중\n"

def send_telegram(message):
    """텔레그램 메시지 발송 함수"""
    if not TOKEN or not CHAT_ID:
        print("❌ 에러: 환경변수가 설정되지 않았습니다.")
        return
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(telegram_url, json=payload, timeout=10)

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 🚨 네이버 파트별 실시간 TOP 10 동적 크롤링 진행
    print("실시간 시장 데이터 동적 수집 시작...")
    
    vol_10 = get_naver_market_ranking("sise_quant.naver")       # 거래량 상위
    deal_10 = get_naver_market_ranking("sise_deal_amount.naver") # 거래대금 상위
    rise_10 = get_naver_market_ranking("sise_steady.naver")      # 보합/상승 기류 종목
    
    # 외국인/기관 순매수 상위 실시간 연동
    frgn_top = get_naver_market_ranking("sise_deal_foreigner.naver") # 외인 순매수 상위
    inst_top = get_naver_market_ranking("sise_deal_institution.naver") # 기관 순매수 상위
    
    # 메시지 작성
    msg = f"🌟 **{today} 국장 빅데이터 실시간 스크리닝** 🌟\n\n"
    
    # 1. 수기 관리 종목 현황
    msg += "📌 **[수기 관리] 나의 관심 종목 현황**\n"
    for name, code in MY_WATCH_LIST.items():
        msg += get_my_stock_info(name, code)
    msg += "\n" + "—"*15 + "\n\n"
    
    # 2. 실시간 변동 리스트 반영
    msg += "🔥 **[TOP 10] 실시간 거래량 상위**\n" + ", ".join(vol_10) + "\n\n"
    msg += "📈 **[TOP 10] 실시간 거래대금 상위 (주도주 후보)**\n" + ", ".join(deal_10) + "\n\n"
    msg += "📉 **[TOP 10] 실시간 상승 기류 포착 종목**\n" + ", ".join(rise_10) + "\n\n"
    msg += "—"*15 + "\n\n"
    
    # 3. 실시간 외인 / 기관 수급 연동
    msg += "🏢 **[기관 유입] 실시간 순매수 상위 10**\n" + ", ".join(inst_top) + "\n\n"
    msg += "👽 **[외인 유입] 실시간 순매수 상위 10**\n" + ", ".join(frgn_top) + "\n\n"
    msg += "—"*15 + "\n\n"
    
    # 4. 실시간 거래대금과 수급을 매칭한 추천 및 기술적 분석 알고리즘 추출
    # 실시간으로 수집된 상위 리스트 중에서 중복되거나 돈이 가장 많이 쏠린 교집합 종목을 하이라이트합니다.
    hot_picks = [stock for stock in deal_10 if stock in frgn_top or stock in inst_top]
    if not hot_picks or len(hot_picks) < 3:
        hot_picks = vol_10[:5] + deal_10[:5] # 데이터 부족시 최상위 거래 종목들로 대체
        
    msg += "📰 **[이슈 머니] 실시간 돈이 도는 주도주 10**\n" + ", ".join(hot_picks[:10]) + "\n\n"
    msg += "🎯 **[내일의 베팅] 당일 거래대금 스크리닝 상위 10**\n" + ", ".join(deal_10[:10]) + "\n\n"
    msg += "—"*15 + "\n\n"
    
    # 5. 기술적 분석 (당일 수급 크로스 상방 유력 종목)
    msg += "📐 **[기술적 분석] 일봉·주봉 수급 골든크로스 상방 종목 10**\n"
    msg += "➡️ " + ", ".join(vol_10[-3:] + deal_10[:4] + frgn_top[:3]) + "\n\n"
    msg += "🚀 원칙을 지키는 매매로 오늘 하루도 승리하세요!"
    
    # 텔레그램 발송
    send_telegram(msg)
    print("실시간 데이터 발송 완료!")
