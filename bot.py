import yfinance as yf
import requests
from datetime import datetime, timedelta

# 1. 텔레그램 설정
TOKEN = '8791795120:AAGOQn6N0W0CcN0rXeuExyz1YMuijU8sYQw'
CHAT_ID = '6437182695'

# 2. 전체 자산 티커 딕셔너리
assets = {
    'S&P 500': 'ES=F',
    '나스닥 100': 'NQ=F',
    '다우존스': 'YM=F',
    '독일 DAX': '^GDAXI',
    '영국 FTSE': '^FTSE',
    '미국 10년물': '^TNX',
    '독일 10년물(Bund)': '^GDBR10',
    '유로/달러': 'EURUSD=X',
    '달러/엔': 'JPY=X',
    '달러/원(NDF)': 'KRW=X',
    '금(Gold)': 'GC=F',
    'WTI유': 'CL=F'
}

def get_data(keys):
    """요청받은 자산 리스트의 데이터를 정제된 텍스트로 반환"""
    text = ""
    for key in keys:
        if key in assets:
            ticker = assets[key]
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if len(hist) < 2: continue
                
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
                
                # 금융권 표준 등락 기호 적용
                sign = "▲" if change_pct > 0 else ("▼" if change_pct < 0 else "-")
                
                # 데이터 성격별 포맷팅 (금리, 환율, 지수)
                if '10년물' in key:
                    text += f" - {key}: {current:.3f}% ({sign}{abs(change_pct):.2f}%)\n"
                elif '원' in key or '엔' in key:
                    text += f" - {key}: {current:.2f} ({sign}{abs(change_pct):.2f}%)\n"
                elif '유로/달러' in key:
                    text += f" - {key}: {current:.4f} ({sign}{abs(change_pct):.2f}%)\n"
                else:
                    text += f" - {key}: {current:,.2f} ({sign}{abs(change_pct):.2f}%)\n"
            except:
                text += f" - {key}: 데이터 확인 불가\n"
    return text

def run_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    
    title = ""
    desc = ""
    priority_1 = ""
    priority_2 = ""
    
    # 시간대별 전문가 시황 분석 코멘트
    if 17 <= hour < 19:
        title = "[17:00] 유럽장 초기 반응 점검"
        desc = "현 시간대는 유럽 기관이 아시아장 결과를 소화하며 포지션을 구축하는 구간입니다. 추세가 반전되는 경우가 잦아 방향성에 대한 신뢰도는 비교적 낮습니다."
        priority_1 = get_data(['독일 DAX', '영국 FTSE', '유로/달러', '금(Gold)', '독일 10년물(Bund)'])
        priority_2 = get_data(['WTI유', '달러/엔'])
        
    elif 19 <= hour < 21:
        title = "[19:00] 프리마켓 방향성 형성 구간"
        desc = "유럽장이 본 궤도에 진입하고 미국 프리마켓 참여자가 증가하면서, 금일 시장의 전체적인 윤곽이 잡히는 시점입니다."
        priority_1 = get_data(['S&P 500', '나스닥 100', '유로/달러', '달러/엔', '금(Gold)', '미국 10년물'])
        priority_2 = get_data(['독일 DAX', 'WTI유', '달러/원(NDF)'])
        
    elif 21 <= hour < 23:
        title = "[22:00] 미국 정규장 개장 및 당일 추세 결정"
        desc = "글로벌 기관 자금이 본격적으로 유입되는 핵심 구간입니다. 개장 후 30~60분간의 흐름이 당일 시장의 방향성을 결정짓는 주요 지표가 됩니다."
        priority_1 = get_data(['S&P 500', '나스닥 100', '미국 10년물', '다우존스'])
        priority_2 = get_data(['유로/달러', '금(Gold)', 'WTI유', '달러/원(NDF)'])
        
    elif 0 <= hour < 2:
        title = "[00:30] 미국장 중반 추세 검증"
        desc = "장 초반의 변동성이 완화되고 기관의 실제 매매 동향이 드러나는 구간입니다. 개장 직후 형성된 방향성이 유지되고 있는지 검증이 필요합니다."
        priority_1 = get_data(['S&P 500', '나스닥 100', '미국 10년물'])
        priority_2 = get_data(['금(Gold)', '유로/달러'])
        
    elif 5 <= hour < 7:
        title = "[06:00] 미국장 마감 및 종가 강도 확인"
        desc = "장 마감 직전 기관의 최종 포지션 조율이 이루어집니다. 형성된 종가의 위치가 익일 아시아 시장의 방향성을 예고합니다."
        priority_1 = get_data(['S&P 500', '나스닥 100', '다우존스', '미국 10년물'])
        priority_2 = get_data(['달러/원(NDF)', '금(Gold)'])
        
    else:
        title = "글로벌 마켓 정기 요약"
        desc = "주요 리스크 자산 및 안전 자산 흐름 점검"
        priority_1 = get_data(['S&P 500', '나스닥 100', '미국 10년물', '유로/달러', '금(Gold)'])
        priority_2 = get_data(['다우존스', '달러/원(NDF)', 'WTI유'])
        
    # 전문적인 형태의 메시지 텍스트 조립
    final_msg = f"{title}\n({now_kst.strftime('%Y-%m-%d %H:%M KST')})\n\n"
    final_msg += f"[시장 브리핑]\n{desc}\n\n"
    final_msg += f"[1순위: 핵심 점검 지표]\n{priority_1}\n"
    if priority_2:
        final_msg += f"[2순위: 보조 점검 지표]\n{priority_2}"
    
    # 텔레그램 전송
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': final_msg}
    
    requests.post(url, data=payload)

if __name__ == "__main__":
    run_report()
