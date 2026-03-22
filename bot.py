import yfinance as yf
import requests
from datetime import datetime, timedelta

# 1. 텔레그램 설정
TOKEN = '8791795120:AAGOQn6N0W0CcN0rXeuExyz1YMuijU8sYQw'
CHAT_ID = '6437182695'

# 2. 핵심 자산 티커 (글자 깨짐 방지를 위해 이름 간소화)
assets = {
    '지수/선물': {
        'S&P 500': 'ES=F',
        '나스닥 100': 'NQ=F',
        '다우존스': '^DJI',
        '독일 DAX': '^GDAXI',
        '영국 FTSE': '^FTSE'
    },
    '국채/외환': {
        '미국 10년물': '^TNX',
        '독일 10년물': '^GDBR10',
        '유로/달러': 'EURUSD=X',
        '달러/엔': 'JPY=X',
        '달러/원(NDF)': 'KRW=X'
    },
    '원자재': {
        '금(Gold)': 'GC=F',
        'WTI유': 'CL=F'
    }
}

def get_data(category, keys):
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
                
                if '금리' in key or '10년물' in key:
                    text += f"▪️ {key}: {current:.3f}% ({emoji}{abs(change_pct):.2f}%)\n"
                elif '원' in key or '엔' in key:
                    text += f"▪️ {key}: {current:.2f} ({emoji}{abs(change_pct):.2f}%)\n"
                else:
                    text += f"▪️ {key}: {current:,.2f} ({emoji}{abs(change_pct):.2f}%)\n"
            except:
                text += f"▪️ {key}: 데이터 지연\n"
    return text + "\n"

def run_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    
    report = ""
    
    # 시간대별 시나리오
    if 17 <= hour < 19:
        title = "🌍 [17:00] 유럽장 초기 반응 (신뢰도 낮음)"
        report += get_data('지수/선물', ['독일 DAX', '영국 FTSE'])
        report += get_data('국채/외환', ['유로/달러', '독일 10년물'])
        report += get_data('원자재', ['금(Gold)'])
    elif 19 <= hour < 21:
        title = "🧭 [19:00] 방향 형성 구간 (프리마켓)"
        report += get_data('지수/선물', ['S&P 500', '나스닥 100'])
        report += get_data('국채/외환', ['미국 10년물', '유로/달러', '달러/엔'])
        report += get_data('원자재', ['금(Gold)', 'WTI유'])
    elif 21 <= hour < 23:
        title = "🔥 [22:00] 미장 개장 및 방향성 확정"
        report += get_data('지수/선물', ['S&P 500', '나스닥 100', '다우존스'])
        report += get_data('국채/외환', ['미국 10년물', '유로/달러'])
        report += get_data('원자재', ['금(Gold)'])
    elif 0 <= hour < 2:
        title = "👀 [00:30] 미장 장중 진짜 추세 확인"
        report += get_data('지수/선물', ['S&P 500', '나스닥 100'])
        report += get_data('국채/외환', ['미국 10년물'])
    elif 5 <= hour < 7:
        title = "🏁 [06:00] 미장 마감 및 종가 강도 확인"
        report += get_data('지수/선물', ['S&P 500', '나스닥 100', '다우존스'])
        report += get_data('국채/외환', ['미국 10년물', '달러/원(NDF)'])
    else:
        title = "📊 마켓 정기 요약"
        report += get_data('지수/선물', ['S&P 500', '나스닥 100'])
        report += get_data('국채/외환', ['미국 10년물', '유로/달러'])
        
    final_msg = f"🗓️ {title}\n({now_kst.strftime('%H:%M KST')})\n\n{report}"
    
    # 텔레그램 전송 (오류를 일으키는 Markdown 옵션 삭제!)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': final_msg}
    
    print("텔레그램 전송 시도...")
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        print("✅ 텔레그램 전송 성공!")
    else:
        print(f"❌ 전송 실패: {res.text}")

if __name__ == "__main__":
    run_report()
