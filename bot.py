import yfinance as yf
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime, timedelta

# 1. 텔레그램 설정
TOKEN = '8791795120:AAGOQn6N0W0CcN0rXeuExyz1YMuijU8sYQw'
CHAT_ID = '-1003856894708'

# 2. 자산 티커 딕셔너리
assets = {
    'S&P 500': 'ES=F',
    '나스닥 100': 'NQ=F',
    '미국 10년물': '^TNX',
    '달러/원(NDF)': 'KRW=X',
    '금(Gold)': 'GC=F',
    'WTI유': 'CL=F',
    '달러 인덱스': 'DX-Y.NYB'
}

def generate_trend_chart():
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
    """종목 데이터와 함께 변동률(%) 값을 같이 반환하도록 수정"""
    ticker = assets[ticker_name]
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if len(hist) < 2: return {'text': None, 'pct': 0}
        
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        change_pct = ((current - prev) / prev) * 100
        sign = "▲" if change_pct > 0 else ("▼" if change_pct < 0 else "-")
        
        if '10년물' in ticker_name: price_str = f"{current:.3f}%"
        elif '원' in ticker_name or '엔' in ticker_name or '인덱스' in ticker_name: price_str = f"{current:.2f}"
        else: price_str = f"{current:,.2f}"
            
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

        comment_str = f" -> {comment}" if comment else ""
        text_result = f"{ticker_name} {price_str} ({sign}{abs(change_pct):.2f}%){comment_str}"
        
        return {'text': text_result, 'pct': change_pct}
    except:
        return {'text': f"{ticker_name} 데이터 확인 불가", 'pct': 0}

def run_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    
    chart_file = generate_trend_chart()
    if chart_file and os.path.exists(chart_file):
        photo_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(chart_file, 'rb') as photo:
            requests.post(photo_url, data={'chat_id': CHAT_ID}, files={'photo': photo})
    
    wti_data = get_market_data('WTI유')
    bond_data = get_market_data('미국 10년물')
    nasdaq_data = get_market_data('나스닥 100')
    dxy_data = get_market_data('달러 인덱스')
    krw_data = get_market_data('달러/원(NDF)')
    
    final_msg = f"[매크로 시황 및 국내 시장 파급 효과 분석]\n기준일시: {now_kst.strftime('%Y-%m-%d %H:%M KST')}\n\n"
    
    final_msg += "■ 전일/당일 글로벌 매크로 동향 (원인)\n"
    if wti_data['text']: final_msg += f"1. 에너지: {wti_data['text']}\n"
    if bond_data['text']: final_msg += f"2. 채권시장: {bond_data['text']}\n"
    if nasdaq_data['text']: final_msg += f"3. 뉴욕증시: {nasdaq_data['text']}\n"
    if dxy_data['text']: final_msg += f"4. 통화시장: {dxy_data['text']}\n\n"
    
    final_msg += "■ 국내 시장 파급 효과 (결과 및 전망)\n"
    if krw_data['text']: final_msg += f"결과: {krw_data['text']}\n"
    
    # --- 다이내믹 Summary 로직 ---
    krw_pct = krw_data['pct']
    nasdaq_pct = nasdaq_data['pct']
    
    summary_text = ""
    
    # 1. 환율(외국인 수급) 평가
    if krw_pct > 0.5:
        summary_text += "환율 상승으로 인한 외국인 수급 이탈 부담이 존재하며, "
    elif krw_pct < -0.5:
        summary_text += "환율 안정세로 외국인 자금 유입 환경이 점차 조성되고 있으며, "
    else:
        summary_text += "환율이 보합세를 보이는 가운데, "

    # 2. 나스닥(투자 심리 및 섹터) 평가
    if nasdaq_pct > 1.0:
        summary_text += "나스닥 호조에 힘입어 국내 반도체, AI, 로봇 등 주요 기술주 섹터 중심의 강력한 매수 심리 개선이 기대됩니다."
    elif nasdaq_pct < -1.0:
        summary_text += "기술주 중심의 나스닥 급락이 국내 증시의 밸류에이션 부담으로 작용할 수 있어 보수적인 방어 접근이 필요합니다."
    else:
        summary_text += "글로벌 지표 변동성을 주시하며 개별 섹터별 차별화 장세에 대비해야 할 시점입니다."
        
    final_msg += f"\n[Summary]\n{summary_text}"
    
    text_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(text_url, data={'chat_id': CHAT_ID, 'text': final_msg})

if __name__ == "__main__":
    run_report()
