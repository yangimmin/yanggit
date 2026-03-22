import yfinance as yf
import requests
from datetime import datetime
import pandas as pd

# 1. 텔레그램 설정 (본인 정보로 수정)
TOKEN = 'YOUR_NEW_TOKEN_HERE' 
CHAT_ID = 'YOUR_CHAT_ID_HERE'

# 2. 조회할 목록
etf_list = {'금융': 'XLF', '에너지': 'XLE', '기술': 'XLK', '헬스케어': 'XLV', '반도체': 'SMH', '석유/가스': 'USO', '금 광업': 'GDX'}
bond_list = {'미국 10년물': '^TNX', '일본 10년물': '^GJGB10', '독일 10년물': '^GDBR10', '영국 10년물': '^GUKG10'}

# 3. 추가된 원자재 목록 (선물 티커 기준)
commodity_list = {
    '금': 'GC=F',
    '은': 'SI=F',
    'WTI유': 'CL=F',
    '구리': 'HG=F',
    '브렌트유': 'BZ=F',
    '천연가스': 'NG=F',
    '난방유': 'HO=F',
    '미국 대두': 'ZS=F',
    '미국 소맥': 'ZW=F',
    '가솔린 RBOB': 'RB=F'
}

def get_market_data(title, ticker_dict, show_volume=False):
    """ETF 및 원자재 데이터를 수집하는 공통 함수 (30일 평균 거래량 포함)"""
    message = f"📊 *{title}*\n\n"
    
    for name, ticker in ticker_dict.items():
        try:
            stock = yf.Ticker(ticker)
            # 30일 평균 거래량을 구하기 위해 30일치 데이터 호출
            hist = stock.history(period="30d") 
            
            if len(hist) < 2:
                continue
                
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            emoji = "🔺" if change_pct > 0 else ("🔻" if change_pct < 0 else "➖")
            
            # 기본 메시지 (가격, 등락률)
            msg_line = f"▪️ *{name}*: ${current_price:.2f} ({emoji}{abs(change_pct):.2f}%)"
            
            # 거래량 표시 옵션이 켜져 있으면 30일 평균 거래량 추가 계산
            if show_volume and 'Volume' in hist.columns:
                avg_vol_30d = hist['Volume'].mean()
                if avg_vol_30d > 0:
                    # 보기 편하게 천 단위 콤마 추가
                    msg_line += f" | 30일 평균 거래량: {int(avg_vol_30d):,}"
            
            message += msg_line + "\n"
            
        except Exception as e:
            message += f"▪️ {name}: 데이터 확인 불가\n"
            
    return message + "\n"

def get_bond_data():
    """국채 금리 데이터를 수집하는 함수"""
    message = "🏛️ *주요 국채 금리 현황 (10년물)*\n\n"
    for name, ticker in bond_list.items():
        try:
            bond = yf.Ticker(ticker)
            hist = bond.history(period="5d")
            if len(hist) < 2: continue
            current_yield = hist['Close'].iloc[-1]
            prev_yield = hist['Close'].iloc[-2]
            change_pct = ((current_yield - prev_yield) / prev_yield) * 100
            emoji = "🔺" if change_pct > 0 else ("🔻" if change_pct < 0 else "➖")
            message += f"▪️ *{name}*: {current_yield:.3f}% ({emoji}{abs(change_pct):.2f}%)\n"
        except:
            message += f"▪️ {name}: 데이터 확인 불가\n"
    return message

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

if __name__ == "__main__":
    print("데이터를 수집 중입니다...")
    
    # 1. ETF 데이터 (거래량 미포함)
    etf_report = get_market_data("오늘의 섹터/테마별 ETF 현황", etf_list)
    # 2. 국채 데이터
    bond_report = get_bond_data()
    # 3. 원자재 데이터 (거래량 포함 옵션 True)
    commodity_report = get_market_data("주요 원자재 현황", commodity_list, show_volume=True)
    
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    final_message = f"🗓️ *[{today}] 마켓 리포트*\n\n" + etf_report + bond_report + commodity_report
    
    send_telegram_message(final_message)
    print("✅ 전송 완료!")
