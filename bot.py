import yfinance as yf
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime, timedelta

# 1. 텔레그램 설정
TOKEN = '8791795120:AAGOQn6N0W0CcN0rXeuExyz1YMuijU8sYQw'
CHAT_ID = '6437182695'

# 2. 자산 티커 딕셔너리
assets = {
    'S&P 500': 'ES=F',
    '나스닥 100': 'NQ=F',
    '미국 10년물': '^TNX',
    '달러/원(NDF)': 'KRW=X',
    '금(Gold)': 'GC=F',
    'WTI유': 'CL=F',
    '달러 인덱스': 'DX-Y.NYB' # 달러 인덱스 추가
}

def generate_trend_chart():
    """S&P 500 및 나스닥 100 차트 생성"""
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle('Core Index Trend & Volume (Last 30 Days)', fontsize=14, fontweight='bold')

    try:
        sp500 = yf.Ticker('ES=F').history(period="1mo")
        ax1.plot(sp500.index, sp500['Close'], color='#00ffcc', linewidth=2, label='S&P 500')
        ax1.set_title('S&P 500 Index', loc='left', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.3)
        ax1_vol = ax1.twinx()
        ax1_vol.bar(sp500.index, sp500['Volume'], color='white', alpha=0.2, width=0.5)
        ax1_vol.set_ylim(0, sp500['Volume'].max() * 3)

        nasdaq = yf.Ticker('NQ=F').history(period="1mo")
        ax2.plot(nasdaq.index, nasdaq['Close'], color='#ff33cc', linewidth=2, label='Nasdaq 100')
        ax2.set_title('Nasdaq 100 Index', loc='left', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.3)
        ax2_vol = ax2.twinx()
        ax2_vol.bar(nasdaq.index, nasdaq['Volume'], color='white', alpha=0.2, width=0.5)
        ax2_vol.set_ylim(0, nasdaq['Volume'].max() * 3)

        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.tight_layout()
        chart_path = 'market_trend.png'
        plt.savefig(chart_path, dpi=150)
        plt.close()
        return chart_path
    except:
        return None

def get_market_data(ticker_name):
    """단일 종목의 가격, 등락률, 그리고 시나리오 코멘트를 반환"""
    ticker = assets[ticker_name]
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if len(hist) < 2: return None
        
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        change_pct = ((current - prev) / prev) * 100
        sign = "▲" if change_pct > 0 else ("▼" if change_pct < 0 else "-")
        
        # 포맷팅
        if '10년물' in ticker_name:
            price_str = f"{current:.3f}%"
        elif '원' in ticker_name or '엔' in ticker_name or '인덱스' in ticker_name:
            price_str = f"{current:.2f}"
        else:
            price_str = f"{current:,.2f}"
            
        # 변동성에 따른 자동 매크로 코멘트 생성 알고리즘
        comment = ""
        if ticker_name == 'WTI유':
            if change_pct > 1.5: comment = "인플레이션 상승 압력, 금리 인하 기대감 축소"
            elif change_pct < -1.5: comment = "에너지 가격 안정, 인플레이션 우려 완화"
            
        elif ticker_name == '미국 10년물':
            if change_pct > 1.5: comment = "단기물 동반 상승 시 달러 자산 매력도 상승 -> 위험자산 이탈 우려"
            elif change_pct < -1.5: comment = "국채 금리 안정화 -> 기술주 및 위험자산 선호도 회복"
            
        elif ticker_name in ['나스닥 100', 'S&P 500']:
            if change_pct < -1.5: comment = "위험자산 기피 심리 확산 -> 안전자산(달러) 수요 폭증"
            elif change_pct > 1.5: comment = "위험자산 선호 심리 강화 -> 주식 시장 자금 유입"
            
        elif ticker_name == '달러/원(NDF)':
            if change_pct > 0.5: comment = "고환율로 인한 외인 자금 이탈 가속화 우려 -> 코스피 하락 압박"
            elif change_pct < -0.5: comment = "환율 안정세 -> 외인 수급 개선 및 코스피 지지력 확보 기대"
            
        elif ticker_name == '달러 인덱스':
            if change_pct > 0.5: comment = "글로벌 달러 강세 독주 -> 원화 등 신흥국 통화 약세 유도"

        # 코멘트가 있으면 추가, 없으면 빈칸
        comment_str = f" -> {comment}" if comment else ""
        return f"{ticker_name} {price_str} ({sign}{abs(change_pct):.2f}%){comment_str}"
        
    except:
        return f"{ticker_name} 데이터 확인 불가"

def run_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    
    # 1. 차트 발송
    chart_file = generate_trend_chart()
    if chart_file and os.path.exists(chart_file):
        photo_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(chart_file, 'rb') as photo:
            requests.post(photo_url, data={'chat_id': CHAT_ID}, files={'photo': photo})
    
    # 2. 데이터 수집 및 시나리오 작성
    wti_data = get_market_data('WTI유')
    bond_data = get_market_data('미국 10년물')
    nasdaq_data = get_market_data('나스닥 100')
    dxy_data = get_market_data('달러 인덱스')
    krw_data = get_market_data('달러/원(NDF)')
    
    # 3. 최종 보고서 조립 (대표님 양식 적용)
    final_msg = f"[매크로 시황 및 국내 시장 파급 효과 분석]\n기준일시: {now_kst.strftime('%Y-%m-%d %H:%M KST')}\n\n"
    
    final_msg += "■ 전일 글로벌 매크로 동향 (원인)\n"
    if wti_data: final_msg += f"1. 에너지: {wti_data}\n"
    if bond_data: final_msg += f"2. 채권시장: {bond_data}\n"
    if nasdaq_data: final_msg += f"3. 뉴욕증시: {nasdaq_data}\n"
    if dxy_data: final_msg += f"4. 통화시장: {dxy_data}\n\n"
    
    final_msg += "■ 국내 시장 파급 효과 (결과 및 전망)\n"
    if krw_data: final_msg += f"결과: {krw_data}\n"
    
    # 종합 결론
    final_msg += "\n[Summary]\n"
    final_msg += "글로벌 지표 변동에 따른 달러 수요 변화가 환율 방향성을 결정하고 있으며, 현재 환율 수준이 향후 코스피 외국인 수급 및 증시 향방의 핵심 트리거로 작용할 전망입니다."
    
    # 4. 텍스트 발송
    text_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(text_url, data={'chat_id': CHAT_ID, 'text': final_msg})

if __name__ == "__main__":
    run_report()
