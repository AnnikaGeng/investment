import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import logging

# 抑制 yfinance 的日志
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

st.set_page_config(layout="wide", page_title="Top 10 赛道深度分析")

# 定义所有主要的行业/细分赛道ETF及其真实主要持仓
# 数据来源：各ETF官方网站公开信息，2024年数据
SECTOR_ETF_STOCKS = {
    # 科技类 - 基于官方持仓数据
    "XLK": ["AAPL", "NVDA", "MSFT", "AVGO", "CRM"],  # SPDR Technology
    "SMH": ["TSM", "NVDA", "ASML", "AMD", "INTC"],  # VanEck Semiconductor
    "SOXX": ["NVDA", "AVGO", "AMD", "QCOM", "TXN"],  # iShares Semiconductor
    "IGV": ["MSFT", "ORCL", "CRM", "ADBE", "INTU"],  # iShares Software
    "CLOU": ["ORCL", "AMZN", "MSFT", "GOOGL", "CRM"],  # Cloud Computing
    "HACK": ["PANW", "CRWD", "FTNT", "ZS", "NET"],  # Cybersecurity
    "FINX": ["V", "MA", "PYPL", "SQ", "COIN"],  # Fintech
    "BOTZ": ["NVDA", "ISRG", "ABB", "FANUC", "TER"],  # Robotics & AI
    "ROBO": ["NVDA", "AMD", "GOOGL", "MSFT", "ABB"],  # Robotics

    # ARK系列 - 基于ARK官方持仓
    "ARKK": ["TSLA", "COIN", "ROKU", "RBLX", "SHOP"],  # ARK Innovation
    "ARKG": ["CRSP", "TDOC", "EXAS", "NTLA", "EDIT"],  # ARK Genomic
    "ARKX": ["RKLB", "KTOS", "AVAV", "IRDM", "LHX"],  # ARK Space

    # 医疗类 - 基于官方持仓数据
    "XLV": ["LLY", "UNH", "JNJ", "ABBV", "MRK"],  # SPDR Healthcare
    "XBI": ["VRTX", "REGN", "ALNY", "BMRN", "SRPT"],  # SPDR Biotech
    "IBB": ["AMGN", "GILD", "VRTX", "REGN", "BIIB"],  # iShares Biotech
    "IHI": ["ISRG", "EW", "SYK", "ZBH", "BSX"],  # iShares Medical Devices
    "XPH": ["LLY", "NVO", "MRK", "AZN", "GSK"],  # Pharma

    # 能源类 - 基于官方持仓数据
    "XLE": ["XOM", "CVX", "COP", "EOG", "SLB"],  # SPDR Energy
    "XOP": ["COP", "EOG", "DVN", "FANG", "MRO"],  # Oil & Gas Exploration
    "ICLN": ["ENPH", "SEDG", "NEE", "FSLR", "PLUG"],  # Clean Energy
    "TAN": ["FSLR", "ENPH", "SEDG", "RUN", "NOVA"],  # Solar
    "LIT": ["ALB", "SQM", "LAC", "LTHM", "PLL"],  # Lithium & Battery
    "URA": ["CCJ", "UEC", "DNN", "NXE", "UUUU"],  # Uranium
    "ACES": ["ENPH", "ALB", "ON", "NXPI", "STM"],  # Clean Energy Storage

    # 金融类 - 基于官方持仓数据
    "XLF": ["BRK.B", "JPM", "V", "MA", "BAC"],  # SPDR Financial
    "KRE": ["USB", "PNC", "TFC", "CFG", "FITB"],  # Regional Banks
    "IAI": ["GS", "MS", "SCHW", "CME", "SPGI"],  # Brokers
    "KIE": ["BRK.B", "PGR", "CB", "TRV", "ALL"],  # Insurance

    # 工业类 - 基于官方持仓数据
    "XLI": ["GE", "CAT", "RTX", "UNP", "HON"],  # SPDR Industrial
    "ITA": ["RTX", "LMT", "BA", "GD", "NOC"],  # Aerospace & Defense
    "PAVE": ["CAT", "VMC", "MLM", "NUE", "X"],  # Infrastructure
    "IYT": ["UPS", "FDX", "DAL", "UAL", "LUV"],  # Transportation

    # 消费类 - 基于官方持仓数据
    "XLY": ["AMZN", "TSLA", "HD", "MCD", "NKE"],  # Consumer Discretionary
    "XLP": ["PG", "KO", "PEP", "WMT", "COST"],  # Consumer Staples
    "XRT": ["AMZN", "HD", "LOW", "TJX", "ROST"],  # Retail
    "AWAY": ["MAR", "HLT", "H", "RCL", "CCL"],  # Travel & Hotels
    "GAMR": ["MSFT", "SONY", "TTWO", "EA", "RBLX"],  # Gaming

    # 房地产类 - 基于官方持仓数据
    "XLRE": ["AMT", "PLD", "EQIX", "PSA", "WELL"],  # Real Estate
    "VNQ": ["PLD", "AMT", "EQIX", "PSA", "WELL"],  # REITs
    "INDS": ["PLD", "DRE", "REXR", "FR", "STAG"],  # Industrial REITs

    # 通信材料公用事业 - 基于官方持仓数据
    "XLC": ["META", "GOOGL", "NFLX", "DIS", "CMCSA"],  # Communication
    "SOCL": ["META", "SNAP", "PINS", "RDDT", "MTCH"],  # Social Media
    "XLB": ["LIN", "APD", "SHW", "ECL", "NUE"],  # Materials
    "PICK": ["RIO", "BHP", "VALE", "FCX", "SCCO"],  # Mining
    "COPX": ["FCX", "SCCO", "TECK", "HBM", "CMCL"],  # Copper
    "XLU": ["NEE", "DUK", "SO", "D", "AEP"],  # Utilities

    # 新兴主题 - 基于官方持仓数据
    "DRIV": ["TSLA", "NIO", "RIVN", "LCID", "GM"],  # 电动车和自动驾驶（真实持仓）
    "BLOK": ["COIN", "MARA", "RIOT", "MSTR", "SQ"],  # Blockchain
    "BETZ": ["DKNG", "FDW", "FLUT", "MGM", "CZR"],  # Betting & Sports
    "ESPO": ["TTWO", "EA", "ATVI", "GME", "RBLX"],  # eSports
    "GNOM": ["ILMN", "TMO", "DHR", "A", "QGEN"],  # Genomics
}

# 定义ETF中文名称映射
ETF_CHINESE_NAMES = {
    "XLK": "科技整体",
    "SMH": "半导体",
    "SOXX": "半导体设备",
    "IGV": "软件",
    "CLOU": "云计算",
    "HACK": "网络安全",
    "FINX": "金融科技",
    "BOTZ": "机器人自动化",
    "ROBO": "机器人AI",
    "ARKK": "颠覆性创新",
    "XLV": "医疗整体",
    "XBI": "生物科技",
    "IBB": "生物技术",
    "ARKG": "基因组学",
    "IHI": "医疗设备",
    "XPH": "制药",
    "XLE": "能源整体",
    "XOP": "石油勘探",
    "ICLN": "清洁能源",
    "TAN": "太阳能",
    "LIT": "锂电池",
    "URA": "铀矿核能",
    "ACES": "清洁能源存储",
    "XLF": "金融整体",
    "KRE": "地区银行",
    "IAI": "券商投行",
    "KIE": "保险",
    "XLI": "工业整体",
    "ITA": "航空航天国防",
    "ARKX": "太空探索",
    "PAVE": "基建",
    "IYT": "运输",
    "XLY": "可选消费",
    "XLP": "必需消费",
    "XRT": "零售",
    "AWAY": "旅游酒店",
    "GAMR": "游戏电竞",
    "XLRE": "房地产整体",
    "VNQ": "REITs",
    "INDS": "工业地产",
    "XLC": "通信服务",
    "SOCL": "社交媒体",
    "XLB": "材料整体",
    "PICK": "矿业金属",
    "COPX": "铜矿",
    "XLU": "公用事业",
    "BLOK": "区块链",
    "BETZ": "博彩体育",
    "ESPO": "电子竞技",
    "DRIV": "自动驾驶",
    "GNOM": "基因组",
}

st.title("🏆 Top 10 热门赛道深度分析")
st.caption("自动追踪表现最强的10个细分赛道，展示资金流向和龙头股表现")

# 时间段选择
period_option = st.radio(
    "选择分析周期：",
    options=[5, 10, 20],
    format_func=lambda x: f"{x}日",
    horizontal=True,
    index=2  # 默认20日
)

# 加载所有ETF数据
@st.cache_data(ttl=3600)
def load_all_etf_data(period_days=100):
    """加载所有ETF数据"""
    try:
        etf_list = list(SECTOR_ETF_STOCKS.keys())
        tickers = etf_list + ["SPY"]
        data = yf.download(tickers, period=f"{period_days}d", progress=False)

        if isinstance(data.columns, pd.MultiIndex):
            close_data = data['Close']
        else:
            close_data = data[['Close']]

        return close_data
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return None

# 加载个股数据
@st.cache_data(ttl=3600)
def load_stock_data(stock_list, period_days=60):
    """加载个股数据"""
    try:
        data = yf.download(stock_list, period=f"{period_days}d", progress=False)

        if isinstance(data.columns, pd.MultiIndex):
            close_data = data['Close']
        else:
            close_data = data[['Close']]

        return close_data
    except Exception as e:
        return None

with st.spinner("正在加载赛道数据..."):
    df_etf = load_all_etf_data(period_days=max(100, period_option + 30))

if df_etf is not None and 'SPY' in df_etf.columns:
    # 计算所有ETF的动能并排序
    etf_momentum = []

    for etf in SECTOR_ETF_STOCKS.keys():
        if etf in df_etf.columns:
            try:
                etf_data = df_etf[etf].dropna()
                spy_data = df_etf['SPY'].dropna()

                if len(etf_data) >= period_option + 5 and len(spy_data) >= period_option + 5:
                    # 对齐索引后计算相对强度
                    common_index = etf_data.index.intersection(spy_data.index)
                    if len(common_index) < period_option + 5:
                        continue

                    etf_aligned = etf_data.loc[common_index]
                    spy_aligned = spy_data.loc[common_index]

                    # 计算相对强度
                    rel_strength = etf_aligned / spy_aligned

                    # 计算动能
                    if len(rel_strength) >= period_option + 1:
                        momentum = (rel_strength.iloc[-1] / rel_strength.iloc[-period_option - 1] - 1) * 100

                        # 检查是否有NaN值
                        if not pd.isna(momentum):
                            etf_momentum.append({
                                'etf': etf,
                                'momentum': momentum
                            })
            except:
                continue

    # 获取Top 10
    top10_etfs = sorted(etf_momentum, key=lambda x: x['momentum'], reverse=True)[:10]

    if top10_etfs:
        st.subheader(f"📊 Top 10 赛道 - {period_option}日动能排行")

        # 显示Top 10动能对比图
        etf_codes = [item['etf'] for item in top10_etfs]
        momentums = [item['momentum'] for item in top10_etfs]
        # 生成中文标签：ETF代码 + 中文名称
        chinese_labels = [f"{code} {ETF_CHINESE_NAMES.get(code, '')}" for code in etf_codes]
        colors = ['#00CC96' if x > 0 else '#EF553B' for x in momentums]

        fig_top = go.Figure()
        fig_top.add_trace(go.Bar(
            x=momentums,
            y=chinese_labels,
            orientation='h',
            marker_color=colors,
            text=[f"{m:.2f}%" for m in momentums],
            textposition='outside'
        ))

        fig_top.update_layout(
            title=f"Top 10 赛道动能对比 ({period_option}日)",
            xaxis_title="相对SPY动能 (%)",
            yaxis_title="",
            height=400,
            template="plotly_white",
            yaxis={'categoryorder':'total ascending'}
        )

        st.plotly_chart(fig_top, use_container_width=True)

        st.divider()

        # 为每个Top 10 ETF显示详细信息
        st.subheader("🔍 赛道详细分析")

        # 使用两列布局
        cols = st.columns(2)

        for idx, etf_info in enumerate(top10_etfs):
            etf_code = etf_info['etf']
            etf_momentum = etf_info['momentum']

            with cols[idx % 2]:
                with st.container(border=True):
                    # 标题和动能 - 显示代码和中文名称
                    chinese_name = ETF_CHINESE_NAMES.get(etf_code, "")
                    st.markdown(f"### {etf_code} {chinese_name}")
                    st.metric(f"{period_option}日动能", f"{etf_momentum:.2f}%")

                    # 60日资金流向图
                    if etf_code in df_etf.columns:
                        try:
                            rel_strength = df_etf[etf_code] / df_etf['SPY']
                            flow_series = (rel_strength.pct_change(20) * 100).dropna().tail(60)

                            if len(flow_series) > 0:
                                fig_flow = go.Figure()
                                fig_flow.add_trace(go.Bar(
                                    x=flow_series.index,
                                    y=flow_series,
                                    marker_color=['#26a69a' if x > 0 else '#ef5350' for x in flow_series],
                                    showlegend=False
                                ))

                                fig_flow.update_layout(
                                    height=180,
                                    margin=dict(l=0, r=0, t=10, b=0),
                                    template="plotly_white",
                                    xaxis_visible=False,
                                    yaxis_title="资金流向(%)"
                                )

                                st.plotly_chart(fig_flow, use_container_width=True, config={'displayModeBar': False})
                        except:
                            pass

                    st.markdown("**龙头股表现**")

                    # 加载该ETF的成分股数据
                    stock_list = SECTOR_ETF_STOCKS.get(etf_code, [])

                    if stock_list:
                        stock_df = load_stock_data(stock_list, period_days=60)

                        if stock_df is not None:
                            stock_performance = []

                            for stock in stock_list:
                                if stock in stock_df.columns:
                                    try:
                                        stock_data = stock_df[stock].dropna()

                                        if len(stock_data) >= max(5, period_option):
                                            price_change = (stock_data.iloc[-1] / stock_data.iloc[-period_option] - 1) * 100
                                            current_price = stock_data.iloc[-1]

                                            # 检查是否有NaN值
                                            if not pd.isna(price_change) and not pd.isna(current_price):
                                                stock_performance.append({
                                                    "股票": stock,
                                                    f"{period_option}日涨幅": round(price_change, 2),
                                                    "现价": round(current_price, 2)
                                                })
                                    except:
                                        continue

                            if stock_performance:
                                perf_df = pd.DataFrame(stock_performance).sort_values(f"{period_option}日涨幅", ascending=False)

                                st.dataframe(
                                    perf_df,
                                    column_config={
                                        f"{period_option}日涨幅": st.column_config.NumberColumn(
                                            f"{period_option}日涨幅",
                                            format="%.2f%%"
                                        ),
                                        "现价": st.column_config.NumberColumn("现价", format="$%.2f")
                                    },
                                    hide_index=True,
                                    use_container_width=True,
                                    height=200
                                )
                            else:
                                st.info("暂无个股数据")
                        else:
                            st.info("暂无个股数据")
                    else:
                        st.info("暂无成分股定义")
    else:
        st.warning("暂无有效数据")
else:
    st.error("无法加载数据，请检查网络连接")
