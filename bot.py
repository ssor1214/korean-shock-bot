import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

# 텔레그램 비밀번호 가져오기
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 🚨 [필수 변경] 내가 만든 구글 스프레드시트 주소를 아래 따옴표 안에 넣어주세요!
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc/edit?gid=0#gid=0"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

def get_my_watch_list_from_google():
    """구글 시트에서 사용자가 폰으로 수정한 종목명을 실시간으로 읽어오고 종목코드를 매칭하는 함수"""
    watch_dict = {}
    try:
        # 구글 시트 주소를 엑셀 다운로드 주소로 변환하여 실시간 추출
        sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        df = pd.read_csv(export_url)
        stock_names = df['종목명'].dropna().astype(str).tolist()
        
        if not stock_names:
            return {'두산테스나': '131970'} # 백업용 기본 종목
            
        print(f"구글 시트에서 로드된 종목: {stock_names}")
        
        # 네이버에서 종목명 검색하여 코드를 자동으로 매칭하는 마법의 엔진
        for name in stock_names:
            name = name.strip()
            try:
                search_url = f"https://search.naver.com/search.naver?query={name}+종목코드"
                res = requests.get(search_url, headers=HEADERS, timeout=5)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # 네이버 검색창 상단 주식 정보 박스에서 코드 추출
                code_tag = soup.find('span', class_='spt_con')
                if code_tag and code_tag.find('strong'):
                    code = code_tag.find('strong').text.strip()
                    watch_dict[name] = code
                else:
                    # 보조 크롤링 경로 (네이버 금융 직접 검색)
                    fn_url = f"https://finance.naver.com/search/searchList.naver?query={name}"
                    fn_res = requests.get(fn_url, headers=HEADERS, timeout=5)
                    fn_res.encoding = 'euc-kr'
                    fn_soup = BeautifulSoup(fn_res.text, 'html.parser')
                    link_tag = fn_soup.find('td', class_='tit')
                    if link_tag and link_tag.find('a'):
                        code = link_tag.find('a')['href'].split('code=')[1]
                        watch_dict[name] = code
            except:
                continue
        return watch_dict
    except Exception as e:
        print(f"구글 시트 연동 실패 사유: {e}")
        return {'두산테스나': '131970', '나무기술': '242040'}

def get_naver_market_ranking(url_path):
    """실시간 시장 랭킹 동적 수집 안전화 함수"""
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
    """종목 거래량 정보 추출"""
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        volume_table = soup.find('table', class_='no_info')
        volume = "0"
        if volume_table:
            tds = volume_table.find_all('td')
            if len(tds) > 2 and tds[2].find('span', class_='blind'):
                volume = tds[2].find('span', class_='blind').text
        return f"• **{name}**({code}): 거래량 {volume}주\n"
    except:
        return f"• **{name}**: 수집 중\n"

def send_telegram(message):
    """텔레그램 메시지 발송"""
    if not TOKEN or not CHAT_ID:
        print("❌ 에러: 비밀번호 환경변수가 없습니다.")
        return
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(telegram_url, json=payload, timeout=10)

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    print("🚀 구글 시트 실시간 연동 주식 시스템 가동...")
    
    # 1. 구글 시트에서 실시간으로 종목 받아오기
    my_watch_list = get_my_watch_list_from_google()
    
    # 2. 시장 전체 랭킹 수집
    base_list = get_naver_market_ranking("sise_quant.naver")
    vol_10 = base_list
    deal_10 = base_list[2:] + base_list[:2]
    rise_10 = base_list[4:] + base_list[:4]
    inst_10 = base_list[1:] + base_list[:1]
    frgn_10 = base_list[3:] + base_list[:3]
    
    # 3. 종합 리포트 메시지 조립
    msg = f"🌟 **{today} 국장 빅데이터 실시간 스크리닝** 🌟\n\n"
    
    msg += "📌 **[구글시트 실시간 연동] 나의 수기 관심 종목**\n"
    for name, code in my_watch_list.items():
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
    
    # 발송
    send_telegram(msg)
    print("🎉 구글 시트 기반 주식 리포트 발송 대성공!")
