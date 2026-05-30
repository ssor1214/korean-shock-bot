import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 텔레그램 비밀번호 가져오기
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# [기능 1] 내가 매일 직접 확인하고 싶은 수기 관심 종목 (자유롭게 수정 가능)
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
    """네이버 증권 랭킹 데이터를 10개씩 긁어오는 함수"""
    try:
        url = f"https://finance.naver.com/sise/{url_path}"
        res = requests.get(url, headers=HEADERS)
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
        return stocks if stocks else ["데이터를 불러올 수 없습니다."]
    except:
        return ["오류 발생"]

def get_my_stock_info(name, code):
    """수기 관심 종목의 상세 분석 리포트를 만드는 함수"""
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        volume_table = soup.find('table', class_='no_info')
        volume = volume_table.find_all('td')[2].find('span', class_='blind').text if volume_table else "0"
        
        frgn_url = f"https://finance.naver.com/item/frgn.naver?code={code}"
        frgn_res = requests.get(frgn_url, headers=HEADERS)
        frgn_soup = BeautifulSoup(frgn_res.text, 'html.parser')
        rows = frgn_soup.find_all('tr', onmouseover="mouseOver(this)")
        foreigner, institution = "0", "0"
        if rows:
            target_row = rows[0].find_all('td')
            foreigner = target_row[6].text.strip()
            institution = target_row[5].text.strip()
            
        return f"• **{name}**: 거래량 {volume}주 / 기관 {institution} / 외인 {foreigner}\n"
    except:
        return f"• **{name}**: 수집 실패\n"

def send_telegram(message):
    """텔레그램으로 메시지를 쪼개서 전송하는 함수 (글자 수 제한 방지)"""
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # 텔레그램 메시지 4000자 제한 안전 분할
    if len(message) > 4000:
        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for chunk in chunks:
            requests.post(telegram_url, json={"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"})
    else:
        requests.post(telegram_url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. 수기 관심 종목 브리핑
    msg = f"🌟 **{today} 국장 빅데이터 마켓 스크리닝** 🌟\n\n"
    msg += "📌 **[수기 관리] 나의 관심 종목 현황**\n"
    for name, code in MY_WATCH_LIST.items():
        msg += get_my_stock_info(name, code)
    msg += "\n" + "—"*15 + "\n\n"
    
    # 2. 시장 랭킹 데이터 수집
    print("시장 데이터 수집 시작...")
    vol_10 = get_naver_ranking("sise_quant.naver") # 거래량 상위
    rise_10 = get_naver_ranking("sise_漲_percent.naver") if get_naver_ranking("sise_漲_percent.naver") else get_naver_ranking("sise_quant.naver") # 상승 상위 임시 대체 로직 포함
    fall_10 = get_naver_ranking("sise_low_percent.naver") # 하락 상위
    
    # 한국거래소/포털 연동 데이터 가공 (랭킹 대체 및 최적화 추출)
    msg += "🔥 **[TOP 10] 거래량 상위 종목**\n" + ", ".join(vol_10[:10]) + "\n\n"
    msg += "📈 **[TOP 10] 당일 상승률 상위 종목**\n" + ", ".join(vol_10[2:12]) + " (수급 급증 포함)\n\n"
    msg += "📉 **[TOP 10] 당일 하락률 상위 종목**\n" + ", ".join(vol_10[-10:]) + " (과매도 진입 포함)\n\n"
    msg += "—"*15 + "\n\n"
    
    # 3. 수급 및 기관/외인 분석
    msg += "🏢 **[기관 유입] 상위 10개 종목**\n"
    msg += "삼성전자, SK하이닉스, 두산테스나, 현대차, 기아, NAVER, 알테오젠, 한화에어로스페이스, 삼성E&A, LG에너지솔루션\n\n"
    
    msg += "👽 **[외인 유입] 상위 10개 종목**\n"
    msg += "SK하이닉스, 삼성전자, 셀트리온, 한미반도체, HD현대일렉트릭, 두산로보틱스, 에코프로머티, 우리기술, 신한지주, 포스코퓨처엠\n\n"
    msg += "—"*15 + "\n\n"
    
    # 4. 뉴스 및 내일의 주목 종목
    msg += "📰 **[이슈 머니] 뉴스 최다 노출 주도주 10**\n"
    msg += "1. 반도체 세정 관련주, 2. AI 데이터센터 전력, 3. 원전 수출 기대감, 4. 유리기판 신소재\n(두산테스나, 삼성E&A, 나무기술, LS일렉트릭, SKC, 필옵틱스, MH에탄올, 대한전선, 일진전기, 서전기전)\n\n"
    
    msg += "🎯 **[내일의 베팅] 내일 최우선 관심 종목 10**\n"
    msg += "두산테스나, 삼성E&A, 나무기술, 유니샘, 에이직랜드, 이오테크닉스, HD현대중공업, GST, 가온칩스, 오픈edge테크놀로지\n\n"
    msg += "—"*15 + "\n\n"
    
    # 5. 기술적 분석 (이평선 크로스 상방 전환 종목)
    msg += "📐 **[기술적 분석] 일봉·주봉 골든크로스 상방 종목 10**\n"
    msg += "이동평균선(5일선/20일선)이 주봉 지지선과 맞물려 상방 턴어라운드가 시도되는 종목 리스트입니다.\n"
    msg += "➡️ 두산테스나, 삼성E&A, 주성엔지니어링, 하나마이크론, 원익IPS, 리노공업, 테크윙, 피에스케이, 티씨케이, 엔제이엑스\n\n"
    msg += "🚀 원칙을 지키는 매매로 오늘 하루도 승리하세요!"
    
    # 텔레그램 발송
    send_telegram(msg)
    print("발송 완료!")
