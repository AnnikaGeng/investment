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

# 初始化session state用于ETF选择
if 'selected_etf' not in st.session_state:
    st.session_state.selected_etf = None


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
            # 可点击的标题链接
            if st.button(f"{ticker} ({current_rank_map[ticker]}位) {diff_text}", key=f"btn_{ticker}", type="secondary", width='stretch'):
                st.session_state.selected_etf = ticker
                st.rerun()

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
                title=f"<span style='font-size:12px;color:gray'>{etf_info[ticker]['name']} | 强度: {val:.2f}%</span>",
                height=280,
                margin=dict(l=10, r=10, t=40, b=10),
                template="plotly_white",
                showlegend=False
            )

            chart_config = {'displayModeBar': False, 'responsive': True}
            st.plotly_chart(fig, config=chart_config, width='stretch')
            
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
                        width='stretch'
                    )
                else:
                    st.info("成分股数据暂无")
            
            st.divider()

    # 6. ETF详情分析区域（按RRG表现排序）
    st.markdown("---")
    st.header("🔍 ETF 详细分析")

    # 创建按RRG表现排序的ETF选项列表（确保使用已排序的结果）
    etf_options = [(f"{item['ticker']} - {etf_info[item['ticker']]['name']} | 动能: {item['latest_val']:+.2f}%", item['ticker'])
                   for item in sorted_results]

    # 如果从上方图表点击跳转，使用session_state中的选择
    if st.session_state.selected_etf:
        # 找到对应的index
        default_index = next((i for i, opt in enumerate(etf_options) if opt[1] == st.session_state.selected_etf), 0)
    else:
        default_index = 0

    selected_display = st.selectbox(
        "选择要分析的ETF（已按RRG表现从高到低排序）",
        options=[opt[0] for opt in etf_options],
        index=default_index
    )

    # 从选择的显示文本中提取ticker
    selected_ticker = [opt[1] for opt in etf_options if opt[0] == selected_display][0]

    # 更新session state
    st.session_state.selected_etf = selected_ticker

    # 显示详细分析
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"{selected_ticker} - {etf_info[selected_ticker]['name']}")

        # 绘制更详细的RRG走势图
        rel_strength = df[selected_ticker] / df[benchmark]
        rotation_series = (rel_strength.pct_change(20) * 100).dropna()

        fig_detail = go.Figure()
        fig_detail.add_trace(go.Scatter(
            x=rotation_series.index,
            y=rotation_series,
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4),
            name='相对强度'
        ))

        # 添加零线
        fig_detail.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        fig_detail.update_layout(
            title=f"{selected_ticker} 相对SPY的20日动能变化趋势",
            height=400,
            template="plotly_white",
            yaxis_title="相对强度 (%)",
            xaxis_title="日期",
            hovermode='x unified'
        )

        st.plotly_chart(fig_detail, width='stretch')

    with col2:
        st.subheader("关键指标")

        # 获取当前排名和变动
        current_rank = current_rank_map[selected_ticker]
        rank_diff = yesterday_rank_map[selected_ticker] - current_rank

        st.metric(
            label="当前排名",
            value=f"第 {current_rank} 名",
            delta=f"{rank_diff}" if rank_diff != 0 else "持平",
            delta_color="normal"
        )

        st.metric(
            label="RRG强度",
            value=f"{rotation_series.iloc[-1]:.2f}%",
            delta=f"{rotation_series.iloc[-1] - rotation_series.iloc[-2]:.2f}%" if len(rotation_series) >= 2 else None
        )

        # 计算ETF自身涨跌幅
        if len(df[selected_ticker]) >= 20:
            etf_change_20d = (df[selected_ticker].iloc[-1] / df[selected_ticker].iloc[-20] - 1) * 100
            st.metric(
                label="20日涨跌幅",
                value=f"{etf_change_20d:.2f}%"
            )

        # 显示主要成分股
        st.markdown("**主要成分股**")
        st.caption(", ".join(etf_info[selected_ticker]['stocks'][:5]))

    # 成分股详细表现
    st.subheader(f"📊 {selected_ticker} 成分股详细表现")

    stock_list = etf_info[selected_ticker]['stocks']
    stock_details = []

    for s in stock_list:
        if s in df.columns:
            try:
                # 获取价格动能
                week_change = (df[s].iloc[-1] / df[s].iloc[-5] - 1) * 100 if len(df) >= 5 else 0
                month_change = (df[s].iloc[-1] / df[s].iloc[-20] - 1) * 100 if len(df) >= 20 else 0
                current_price = df[s].iloc[-1]

                # 获取 PE 数据
                s_ticker = yf.Ticker(s)
                pe = s_ticker.info.get('trailingPE', None)
                market_cap = s_ticker.info.get('marketCap', 0) / 1e9

                stock_details.append({
                    "代码": s,
                    "周涨幅%": round(week_change, 2),
                    "月涨幅%": round(month_change, 2),
                    "当前价格": round(current_price, 2),
                    "PE (TTM)": round(pe, 2) if pe and pe != "N/A" else "N/A",
                    "市值 (B)": round(market_cap, 2) if market_cap else "N/A"
                })
            except:
                continue

    if stock_details:
        details_df = pd.DataFrame(stock_details).sort_values("月涨幅%", ascending=False)

        st.dataframe(
            details_df,
            hide_index=True,
            column_config={
                "周涨幅%": st.column_config.NumberColumn("周涨幅%", format="%.2f%%"),
                "月涨幅%": st.column_config.NumberColumn("月涨幅%", format="%.2f%%"),
                "当前价格": st.column_config.NumberColumn("当前价格", format="$%.2f"),
                "PE (TTM)": st.column_config.TextColumn("PE (TTM)", help="滚动市盈率"),
                "市值 (B)": st.column_config.NumberColumn("市值 (B)", format="%.2f", help="市值（十亿美元）")
            },
            width='stretch',
            height=400
        )

except Exception as e:
    st.error(f"数据加载失败，请检查网络连接或稍后再试。错误: {e}")
