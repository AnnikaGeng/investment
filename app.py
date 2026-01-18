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

st.title("📊 全球板块资金流向全景图 (按强度排序)")
st.markdown("计算说明：显示各板块相对于 SPY 的 20 日动能变化 (Capital Rotation Rel) + 成分股表现分析")

# 2. 获取数据
benchmark = "SPY"
tickers = list(etf_info.keys()) + [benchmark]
# 收集所有成分股用于分析
all_stocks = []
for info in etf_info.values():
    all_stocks.extend(info['stocks'])
all_stocks = list(set(all_stocks))  # 去重

@st.cache_data(ttl=3600) # 缓存1小时
def load_data(ticker_list, stock_list):
    data = yf.download(ticker_list + stock_list, period="1y")['Close']
    return data

try:
    df = load_data(tickers, all_stocks)
    
    # 3. 计算排名与位次变动（带缓存）
    @st.cache_data(ttl=3600)
    def calculate_rankings(df_data):
        rotation_results = []
        for ticker in etf_info.keys():
            # 相对强弱逻辑：(ETF / SPY) 的 20 日变化率
            rel_strength = df_data[ticker] / df_data[benchmark]
            rotation_series = (rel_strength.pct_change(20) * 100).dropna()
            latest_val = rotation_series.iloc[-1]
            
            rotation_results.append({
                "ticker": ticker,
                "latest_val": latest_val,
                "series": rotation_series
            })
        
        # 执行排序：按最新数值从大到小排列
        sorted_results = sorted(rotation_results, key=lambda x: x['latest_val'], reverse=True)
        
        # 计算排名变动（今日 vs 昨日）
        current_ranks = {item['ticker']: i + 1 for i, item in enumerate(sorted_results)}
        yesterday_results = []
        
        for ticker in etf_info.keys():
            rel_strength = df_data[ticker] / df_data[benchmark]
            rotation_series = (rel_strength.pct_change(20) * 100).dropna()
            # 取前一天的值
            if len(rotation_series) >= 2:
                yesterday_val = rotation_series.iloc[-2]
            else:
                yesterday_val = rotation_series.iloc[-1]
            yesterday_results.append({
                "ticker": ticker,
                "val": yesterday_val
            })
        
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
            
            # 成分股表现监控与PE分析（可展开）
            with st.expander(f"📈 {ticker} 领涨个股及估值分析"):
                stock_list = etf_info[ticker]['stocks']
                stock_details = []
                
                for s in stock_list:
                    if s in df.columns:
                        # 获取价格动能
                        week_change = (df[s].iloc[-1] / df[s].iloc[-5] - 1) * 100 if len(df) >= 5 else 0
                        current_price = df[s].iloc[-1]
                        
                        # 获取 PE 数据 (使用 yfinance 的 Ticker 对象)
                        try:
                            s_ticker = yf.Ticker(s)
                            pe = s_ticker.info.get('trailingPE', "N/A")  # 获取滚动市盈率
                            market_cap = s_ticker.info.get('marketCap', 0) / 1e9  # 转换成 B (十亿)
                        except:
                            pe = "N/A"
                            market_cap = "N/A"
                        
                        stock_details.append({
                            "代码": s,
                            "周涨幅%": round(week_change, 2),
                            "当前价格": round(current_price, 2),
                            "PE (TTM)": pe,
                            "市值 (B)": round(market_cap, 2) if market_cap != "N/A" else "N/A"
                        })
                
                if stock_details:
                    # 转换为 DataFrame 并排序
                    details_df = pd.DataFrame(stock_details).sort_values("周涨幅%", ascending=False)
                    
                    # 使用 Streamlit 的表格增强显示
                    st.dataframe(
                        details_df,
                        hide_index=True,
                        column_config={
                            "PE (TTM)": st.column_config.NumberColumn("PE (TTM)", help="滚动市盈率，越高代表估值越高"),
                            "周涨幅%": st.column_config.NumberColumn("周涨幅%", format="%.2f%%", help="周涨跌幅：正数表示上涨，负数表示下跌")
                        },
                        use_container_width=True
                    )
                else:
                    st.info("成分股数据暂无")
            
            st.divider()

except Exception as e:
    st.error(f"数据加载失败，请检查网络连接或稍后再试。错误: {e}")