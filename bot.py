import yfinance as yf
import requests
from datetime import datetime, timedelta

# 1. 텔레그램 설정
TOKEN = '8791795120:AAGOQn6N0W0CcN0rXeuExyz1YMuijU8sYQw'
CHAT_ID = '6437182695'

# 2. 핵심 자산 티커 딕셔너리 (노이즈 제거, 핵심만)
assets = {
    '지수/선물': {
        'S&P 500 (ES선물)': 'ES=F',
        '나스닥 100 (NQ선물)': 'NQ=F',
        '다우존스': '^DJI',
        '독일 DAX': '^GDAXI',
        '영국 FTSE': '^FTSE'
    },
    '국채/외환': {
        '미국 10년물 금리': '^TNX',
        '독일 10년물 금리': '^GDBR10',
        '유로/달러 (EUR/USD)': 'EURUSD=X',
        '달러/엔 (USD/JPY)': 'JPY=X',
        '달러/원 (USD/KRW) NDF': 'KRW=X'
    },
    '원자재': {
        '금 (Gold)': 'GC=F',
        'WTI유': 'CL=F'
    }
}

def get_data(category, keys):
    """지정된 카테고리에서 특정 키(항목)의 데이터만 추출"""
    text = ""
    for key in keys:
        if key in assets[category]:
            ticker = assets[category][key]
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if len(hist) < 2: continue
                
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
                emoji = "🔺" if change_pct > 0 else ("🔻" if change_pct < 0 else "➖")
                
                # 금리는 소수점 3자리, 환율/지수는 2자리 등 포맷팅
                if '금리' in key:
                    text += f"▪️ *{key}*: {current:.3f}% ({emoji}{abs(change_pct):.2f}%)\n"
                elif '원' in key or '엔' in key:
                    text += f"▪️ *{key}*: {current:.2f} ({emoji}{abs(change_pct):.2f}%)\n"
                else:
                    text += f"▪️ *{key}*: {current:,.2f} ({emoji}{abs(change_pct):.2f}%)\n"
            except:
                text += f"▪️ {key}: 데이터 지연\n"
    return text + "\n"

def run_report():
    # 현재 한국 시간 계산
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    
    report = ""
    
    # 시간대별 시나리오 분기
    if 17 <= hour < 19:
        title = "🌍 [17:00] 유럽장 초기 반응 (신뢰도 낮음)"
        report += get_data('지수/선물', ['독일 DAX', '영국 FTSE'])
        report += get_data('국채/외환', ['유로/달러 (EUR/USD)', '독일 10년물 금리'])
        report += get_data('원자재', ['금 (Gold)'])
        
    elif 19 <= hour < 21:
        title = "🧭 [19:00] 방향 형성 구간 (프리마켓)"
        report += get_data('지수/선물', ['S&P 500 (ES선물)', '나스닥 100 (NQ선물)'])
        report += get_data('국채/외환', ['미국 10년물 금리', '유로/달러 (EUR/USD)', '달러/엔 (USD/JPY)'])
        report += get_data('원자재', ['금 (Gold)', 'WTI유'])
        
    elif 21 <= hour < 23:
        title = "🔥 [22:00] 미장 개장 및 방향성 확정 (기관 개입)"
        report += get_data('지수/선물', ['S&P 500 (ES선물)', '나스닥 100 (NQ선물)', '다우존스'])
        report += get_data('국채/외환', ['미국 10년물 금리', '유로/달러 (EUR/USD)'])
        report += get_data('원자재', ['금 (Gold)'])
        
    elif 0 <= hour < 2:
        title = "👀 [00:30] 미장 장중 진짜 추세 확인"
        report += get_data('지수/선물', ['S&P 500 (ES선물)', '나스닥 100 (NQ선물)'])
        report += get_data('국채/외환', ['미국 10년물 금리'])
        
    elif 5 <= hour < 7:
        title = "🏁 [06:00] 미장 마감 및 종가 강도 확인"
        report += get_data('지수/선물', ['S&P 500 (ES선물)', '나스닥 100 (NQ선물)', '다우존스'])
        report += get_data('국채/외환', ['미국 10년물 금리', '달러/원 (USD/KRW) NDF'])
        
    else:
        title = "📊 마켓 정기 요약"
        report += get_data('지수/선물', ['S&P 500 (ES선물)', '나스닥 100 (NQ선물)'])
        report += get_data('국채/외환', ['미국 10년물 금리', '유로/달러 (EUR/USD)'])
        
    final_msg = f"🗓️ *{title}*\n({now_kst.strftime('%H:%M KST')})\n\n{report}"
    
    # 텔레그램 전송
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': final_msg, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

if __name__ == "__main__":
    run_report()
