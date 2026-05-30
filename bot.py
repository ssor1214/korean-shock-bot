import os
import requests
import pandas as pd
import time
from datetime import datetime
from bs4 import BeautifulSoup

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SHEET_ID = "1GjxNLRM2dlHqB6GebW73iFd3IEm4YLobzQqfCJBwwAc"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def get_my_watch_list():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        return {str(row.iloc[0]): str(row.iloc[1]) for _, row in df.iterrows() if pd.notna(row.iloc[0])}
    except:
        return {'두산테스나': '131970'}

def get_stock_technical(code):
    """KRX 데이터 기반 이동평균선 계산 (일봉 기준)"""
    try:
        url = f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=day&count=60&requestType=0"
        res = requests.get(url, headers=HEADERS)
        data = [line.split('|') for line in res.text.split('\n') if len(line.split('|')) > 4]
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'vol'])
        df['close'] = df['close'].astype(int)
        
        # 5일선, 20일선 계산
        ma5 = df['close'].rolling(window=5).mean()
        ma20 = df['close'].rolling(window=20).mean()
        
        if ma5.iloc[-1] > ma20.iloc[-1] and ma5.iloc[-2] <= ma20.iloc[-2]:
            return "골든크로스 발생"
        return "추세 관찰"
    except:
        return "데이터 없음"

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    watch_list = get_my_watch_list()
    
    msg = f"🌟 {today} 정밀 리포트 🌟\n\n📌 [관심 종목 분석]\n"
    for name, code in watch_list.items():
        trend = get_stock_technical(code)
        msg += f"• {name} | 추세: {trend}\n"
    
    msg += "\n🚀 원칙 매매로 승리하세요!"
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
