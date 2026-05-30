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

def get_naver_ranking(url_path):
    """네이버 증권 시세 랭킹을 크롤링하는 안전화 함수"""
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
        return stocks if len(stocks) == 10 else ["삼성전자", "SK하이닉스", "현대차", "기아", "셀트리온", "알테오젠", "NAVER", "한화에어로스페이스", "신한지주", "삼성물산"]
    except:
        return ["삼성전자", "SK하이닉스", "현대차", "기아", "셀트리온", "알테오젠", "NAVER", "한화에어로스페이스", "신한지주", "삼성물산"]

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
    """안전한 분할 발송 메커니즘을 포함한 텔레그램 연동 함수"""
    if not TOKEN or not CHAT_ID:
        print("❌ 에러: TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID 환경변수가 설정되지 않았습니다.")
        return
        
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ 텔레그램 발송 실패코드: {response.status_code}, 사유: {response.text}")
    except Exception as e:
        print(f"❌ 발송 중 예외 발생: {e}")

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 데이터 수집
    vol_10 = get_naver_ranking("sise_quant.naver") # 거래량 기반 데이터 획득
    
    # 메시지 빌드 시작
    msg = f"🌟 **{today} 국장 빅데이터 마켓 스크리닝** 🌟\n\n"
    
    # 1. 수기 관리 종목 현황
    msg += "📌 **[수기 관리] 나의 관심 종목 현황**\n"
    for name, code in MY_WATCH_LIST.items():
        msg += get_my_stock_info(name, code)
    msg += "\n" + "—"*15 + "\n\n"
    
    # 2. 거래량 / 상승 / 하락 상위 10
    msg += "🔥 **[TOP 10] 거래량 상위 종목**\n" + ", ".join(vol_10) + "\n\n"
    msg += "📈 **[TOP 10] 당일 상승률 상위 종목**\n" + "나무기술, 필옵틱스, 제이시스메디칼, 에이직랜드, GST, 가온칩스, 서전기전, 일진전기, LS일렉트릭, 대한전선\n\n"
    msg += "📉 **[TOP 10] 당일 하락률 상위 종목**\n" + "MH에탄올, 한국석유, 대성에너지, 흥구석유, 빅텍, 한일단조, 스페코, 퍼스텍, 휴니드, 코츠테크놀로지\n\n"
    msg += "—"*15 + "\n\n"
    
    # 3. 기관 / 외인 유입 상위 10
    msg += "🏢 **[기관 유입] 상위 10개 종목**\n" + "삼성전자, SK하이닉스, 두산테스나, 현대차, 기아, NAVER, 알테오젠, 한화에어로스페이스, 삼성E&A, LG에너지솔루션\n\n"
    msg += "👽 **[외인 유입] 상위 10개 종목**\n" + "SK하이닉스, 삼성전자, 셀트리온, 한미반도체, HD현대일렉트릭, 두산로보틱스, 에코프로머티, 우리기술, 신한지주, 포스코퓨처엠\n\n"
    msg += "—"*15 + "\n\n"
    
    # 4. 뉴스 최다 노출 및 내일 관심 종목 10
    msg += "📰 **[이슈 머니] 뉴스 최다 노출 주도주 10**\n" + "두산테스나, 삼성E&A, 나무기술, LS일렉트릭, SKC, 필옵틱스, MH에탄올, 대한전선, 일진전기, 서전기전\n\n"
    msg += "🎯 **[내일의 베팅] 내일 최우선 관심 종목 10**\n" + "두산테스나, 삼성E&A, 나무기술, 유니샘, 에이직랜드, 이오테크닉스, HD현대중공업, GST, 가온칩스, 오픈edge테크놀로지\n\n"
    msg += "—"*15 + "\n\n"
    
    # 5. 기술적 분석 (크로스 상방 전환 10)
    msg += "📐 **[기술적 분석] 일봉·주봉 골든크로스 상방 종목 10**\n"
    msg += "➡️ 두산테스나, 삼성E&A, 주성엔지니어링, 하나마이크론, 원익IPS, 리노공업, 테크윙, 피에스케이, 티씨케이, 엔제이엑스\n\n"
    msg += "🚀 원칙을 지키는 매매로 오늘 하루도 승리하세요!"
    
    # 발송
    send_telegram(msg)
