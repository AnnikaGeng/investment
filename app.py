import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 配置页面
st.set_page_config(layout="wide", page_title="板块资金流向监控")

# 定义 ETF 板块及其主要成分 (根据图片信息)
etf_info = {
    "XLK": {"name": "科技 (Technology)", "stocks": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "ADBE", "CRM", "CSCO", "INTU", "META"]},
    "XBI": {"name": "生物科技 (Biotech)", "stocks": ["VRTX", "AMGN", "REGN", "ILMN", "EXAS", "INCYT", "ALKS", "HALO", "VERV", "RGEN"]},
    "XLE": {"name": "能源 (Energy)", "stocks": ["XOM", "CVX", "COP", "SLB", "MPC", "EOG", "OKE", "PSX", "HAL", "BKR"]},
    "XLF": {"name": "金融 (Financials)", "stocks": ["JPM", "BAC", "WFC", "MS", "GS", "BLK", "AXP", "USB", "BK", "PNC"]},
    "XLI": {"name": "工业 (Industrial)", "stocks": ["GE", "HON", "CAT", "UPS", "LMT", "BA", "RTX", "DE", "MMM", "ETN"]},
    "XLV": {"name": "医疗 (Healthcare)", "stocks": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "AZN", "AMZN", "ELI", "VRTX"]},
    "XLY": {"name": "可选消费 (Consumer Disc)", "stocks": ["AMZN", "TSLA", "BABA", "MCD", "SBUX", "NFLX", "NKE", "HD", "LOW", "RCL"]},
    "XLB": {"name": "材料 (Materials)", "stocks": ["LIN", "NUE", "SHW", "APD", "ECL", "FCX", "CLF", "KIM", "ALB", "DOW"]},
    "XLP": {"name": "必选消费 (Staples)", "stocks": ["PG", "KO", "MO", "KR", "WMT", "GIS", "CAG", "ADM", "CLX", "UL"]},
    "XLU": {"name": "公用事业 (Utilities)", "stocks": ["NEE", "DUK", "SO", "D", "AES", "DTE", "EXC", "EIX", "ED", "NRG"]},
    "XLRE": {"name": "房地产 (Real Estate)", "stocks": ["AMT", "PLD", "EQIX", "DLR", "WELL", "AVB", "SPG", "ARE", "EQR", "UMH"]},
    "XLC": {"name": "通信服务 (Communication)", "stocks": ["META", "GOOGL", "GOOG", "VZ", "T", "CMCSA", "CHTR", "NXST", "LYV", "ATVI"]},
    "ARKG": {"name": "基因创新 (Genomics)", "stocks": ["CRSP", "TDOC", "EDIT", "VEEV", "GILD", "SDGR", "SQ", "BEAM", "ZM", "VCYT"]},
    "ARKK": {"name": "颠覆性创新 (Innovation)", "stocks": ["TSLA", "ROKU", "COIN", "ZOOM", "RBLX", "PRLX", "EXAS", "NVTA", "Z", "DESKP"]},
    "ARKX": {"name": "航天太空 (Space)", "stocks": ["RKLB", "LMT", "AVAV", "IRDM", "NOC", "RTX", "VSAT", "SPCE", "AXL", "MAXR"]}
}

st.title("📊 全球板块资金流向图")
st.markdown("计算说明：显示各板块相对于 SPY 的 20 日动能变化 (Capital Rotation Rel) + 成分股表现分析")
st.caption(f"📊 数据最后更新：{pd.Timestamp.now().strftime('%Y年%m月%d日 %H:%M:%S')} (当天缓存，同日内无需重新加载)")


# 2. 获取数据
benchmark = "SPY"
tickers = list(etf_info.keys()) + [benchmark]

@st.cache_data(ttl=86400) # 缓存24小时（当天）
def load_data(ticker_list):
    data = yf.download(ticker_list, period="1y", progress=False)['Close']
    return data

try:
    df = load_data(tickers)
    
    # 3. 计算排名与位次变动（带缓存）
    @st.cache_data(ttl=86400)
    def calculate_rankings(df_data):
        rotation_results = []
        for ticker in etf_info.keys():
            if ticker not in df_data.columns or benchmark not in df_data.columns:
                continue

            try:
                # 对齐索引后计算相对强度
                ticker_data = df_data[ticker].dropna()
                spy_data = df_data[benchmark].dropna()

                # 确保有足够数据
                if len(ticker_data) < 25 or len(spy_data) < 25:
                    continue

                common_index = ticker_data.index.intersection(spy_data.index)
                if len(common_index) < 25:
                    continue

                ticker_aligned = ticker_data.loc[common_index]
                spy_aligned = spy_data.loc[common_index]

                # 相对强弱逻辑：(ETF / SPY) 的 20 日变化率
                rel_strength = ticker_aligned / spy_aligned
                rotation_series = (rel_strength.pct_change(20, fill_method=None) * 100).dropna()

                if len(rotation_series) == 0:
                    continue

                latest_val = rotation_series.iloc[-1]

                if pd.isna(latest_val):
                    continue

                rotation_results.append({
                    "ticker": ticker,
                    "latest_val": latest_val,
                    "series": rotation_series
                })
            except Exception as e:
                continue

        if not rotation_results:
            return [], {}, {}

        # 执行排序：按最新数值从大到小排列
        sorted_results = sorted(rotation_results, key=lambda x: x['latest_val'], reverse=True)

        # 计算排名变动（今日 vs 昨日）
        current_ranks = {item['ticker']: i + 1 for i, item in enumerate(sorted_results)}
        yesterday_results = []

        for ticker in etf_info.keys():
            if ticker not in df_data.columns or benchmark not in df_data.columns:
                continue

            try:
                ticker_data = df_data[ticker].dropna()
                spy_data = df_data[benchmark].dropna()

                if len(ticker_data) < 25 or len(spy_data) < 25:
                    continue

                common_index = ticker_data.index.intersection(spy_data.index)
                if len(common_index) < 25:
                    continue

                ticker_aligned = ticker_data.loc[common_index]
                spy_aligned = spy_data.loc[common_index]

                rel_strength = ticker_aligned / spy_aligned
                rotation_series = (rel_strength.pct_change(20, fill_method=None) * 100).dropna()

                if len(rotation_series) == 0:
                    continue

                # 取前一天的值
                if len(rotation_series) >= 2:
                    yesterday_val = rotation_series.iloc[-2]
                else:
                    yesterday_val = rotation_series.iloc[-1]

                if pd.isna(yesterday_val):
                    continue

                yesterday_results.append({
                    "ticker": ticker,
                    "val": yesterday_val
                })
            except Exception as e:
                continue

        yesterday_sorted = sorted(yesterday_results, key=lambda x: x['val'], reverse=True)
        yesterday_ranks = {item['ticker']: i + 1 for i, item in enumerate(yesterday_sorted)}

        return sorted_results, current_ranks, yesterday_ranks
    
    sorted_results, current_rank_map, yesterday_rank_map = calculate_rankings(df)

    # 5. 布局展示：每行 3 个图表
    cols = st.columns(3)
    
    for i, item in enumerate(sorted_results):
        ticker = item['ticker']
        val = item['latest_val']
        series = item['series'].tail(60) # 只显示最近60天，保持紧凑
        
        # 计算排名变动
        rank_diff = yesterday_rank_map[ticker] - current_rank_map[ticker]
        diff_text = f"+{rank_diff}" if rank_diff > 0 else f"{rank_diff}"
        diff_color = "green" if rank_diff > 0 else ("red" if rank_diff < 0 else "gray")
        
        with cols[i % 3]:
            # 颜色逻辑：正绿负红
            colors = ['#26a69a' if v >= 0 else '#ef5350' for v in series]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=series.index,
                y=series,
                marker_color=colors
            ))
            
            # 图表样式设置
            fig.update_layout(
                title=f"<b>{ticker}</b> ({current_rank_map[ticker]}位) <span style='color:{diff_color}'>{diff_text}</span><br><span style='font-size:12px;color:gray'>{etf_info[ticker]['name']} | 强度: {val:.2f}%</span>",
                height=300,
                margin=dict(l=10, r=10, t=70, b=10),
                template="plotly_white",
                showlegend=False
            )
            
            chart_config = {'displayModeBar': False, 'responsive': True}
            st.plotly_chart(fig, config=chart_config, use_container_width=True)
            
            # 显示主要成分说明
            st.caption(f"主要成分: {', '.join(etf_info[ticker]['stocks'][:5])}")
            
            st.divider()

except Exception as e:
    st.error(f"数据加载失败，请检查网络连接或稍后再试。错误: {e}")
