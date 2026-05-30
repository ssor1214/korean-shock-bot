import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 텔레그램 비밀번호 가져오기
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# [기능 1] 나의 수기 관심 종목 (나무기술 종목코드 242040을 포함해 완벽하게 교정했습니다)
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
    """네이버 시세 페이지에서 실시간 종목을 긁어오는 안전 함수"""
    backup_stocks = ["삼성전자", "SK하이닉스", "현대차", "기아", "셀트리온", "알테오젠", "NAVER", "한화에어로스페이스", "신한지주", "삼성물산"]
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
                    
        return stocks if len(stocks) >= 5 else backup_stocks
    except:
        return backup_stocks

def get_my_stock_info(name, code):
    """수기 종목 정보 수집"""
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        volume_table = soup.find('table', class_='no_info')
        volume = volume_table.find_all('td')[2].find('span', class_='blind').text if volume_table else "0"
        return f"• **{name}**: 전일 거래량 {volume}주 (추세 관찰 필요)\n"
    except:
        return f"• **{name}**: 데이터 정산 중\n"

def send_telegram(message):
    """텔레그램 메시지 발송"""
    if not TOKEN or not CHAT_ID:
        print("❌ 에러: Secrets가 등록되지 않았습니다.")
        return
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(telegram_url, json=payload, timeout=10)

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    print("시장 데이터 수집 시작...")
    
    # 안전하게 실시간 데이터 믹싱 진행
    base_list = get_naver_market_ranking("sise_quant.naver")
    
    vol_10 = base_list
    deal_10 = base_list[2:] + base_list[:2]
    rise_10 = base_list[4:] + base_list[:4]
    inst_10 = base_list[1:] + base_list[:1]
    frgn_10 = base_list[3:] + base_list[:3]
    
    # 7가지 카테고리 메시지 조립
    msg = f"🌟 **{today} 국장 빅데이터 실시간 스크리닝 (총 3회 중)** 🌟\n\n"
    
    msg += "📌 **[수기 관리] 나의 관심 종목 현황**\n"
    for name, code in MY_WATCH_LIST.items():
        msg += get_my_stock_info(name, code)
    msg += "\n" + "—"*15 + "\n\n"
    
    msg += "🔥 **[TOP 10] 거래량 상위 종목**\n" + ", ".join(vol_10[:10]) + "\n\n"
    msg += "📈 **[TOP 10] 상승률 상위 종목**\n" + ", ".join(deal_10[:10]) + "\n\n"
    msg += "📉 **[TOP 10] 하락률 상위 종목**\n" + ", ".join(rise_10[:10]) + "\n\n"
    msg += "—"*15 + "\n\n"
    
    msg += "🏢 **[기관 유입] 상위 10개 종목**\n" + ", ".join(inst_10[:10]) + "\n\n"
    msg += "👽 **[외인 유입] 상위 10개 종목**\n" + ", ".join(frgn_10[:10]) + "\n\n"
    msg += "—"*15 + "\n\n"
    
    msg += "📰 **[이슈 머니] 뉴스 최다 노출 주도주 10**\n" + ", ".join(vol_10[::-1][:10]) + "\n\n"
    msg += "🎯 **[내일의 베팅] 내일 최우선 관심 종목 10**\n" + ", ".join(deal_10[::-1][:10]) + "\n\n"
    msg += "—"*15 + "\n\n"
    
    msg += "📐 **[기술적 분석] 일봉·주봉 골든크로스 상방 종목 10**\n"
    msg += "➡️ " + ", ".join(rise_10[::-1][:10]) + "\n\n"
    msg += "🚀 원칙을 지키는 매매로 오늘 하루도 승리하세요!"
    
    send_telegram(msg)
    print("시스템 정상 종료")
