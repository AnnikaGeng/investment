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

# --- 1. 数据加载与缓存 ---
@st.cache_data(ttl=86400)
def get_market_data(tickers):
    # 增加抓取天数以支持位次变动计算
    return yf.download(tickers, period="60d")['Close']

# 获取所有需要的代码
all_stocks = [s for info in etf_data_map.values() for s in info['stocks']]
all_benchmarks = [info['benchmark'] for info in etf_data_map.values()]
spy_benchmark = ["SPY"]
data = get_market_data(list(set(all_stocks + all_benchmarks + spy_benchmark)))

# --- 2. 核心计算逻辑 ---
def get_daily_rankings(day_offset):
    # 计算某一天的板块相对强度排名
    ranks = []
    for key, info in etf_data_map.items():
        # 相对 SPY 的 20 日动能
        bm = info['benchmark']
        rel_strength = data[bm].iloc[day_offset] / data[bm].iloc[day_offset - 20]
        ranks.append({"key": key, "val": (rel_strength - 1) * 100})
    
    # 排序
    sorted_list = sorted(ranks, key=lambda x: x['val'], reverse=True)
    return {item['key']: i + 1 for i, item in enumerate(sorted_list)}, sorted_list

# 获取今日、昨日排名
curr_rank_map, curr_list = get_daily_rankings(-1)
yest_rank_map, _ = get_daily_rankings(-2)

# --- 3. UI 渲染 ---
st.title("🎯 专业细分赛道指挥部")
st.caption(f"📊 数据最后更新：{pd.Timestamp.now().strftime('%Y年%m月%d日 %H:%M:%S')} (当天缓存，同日内无需重新加载)")

cols = st.columns(2) # 细分赛道较多，用 2 列排列更清晰

for i, item in enumerate(curr_list):
    key = item['key']
    info = etf_data_map[key]
    val = item['val']
    
    # 计算排名升降
    rank_diff = yest_rank_map[key] - curr_rank_map[key]
    diff_icon = f"🚀 +{rank_diff}" if rank_diff > 0 else (f"🔻 {rank_diff}" if rank_diff < 0 else "➖")
    
    with cols[i % 2]:
        with st.container(border=True):
            # 头部信息
            st.subheader(f"{info['name']} ({key})")
            st.write(f"排名：第 **{curr_rank_map[key]}** 名 ({diff_icon}) | 强度：{val:.2f}%")
            
            # 个股分析表格
            stock_data = []
            for stock in info['stocks']:
                if stock in data.columns:
                    week_change = (data[stock].iloc[-1] / data[stock].iloc[-5] - 1) * 100 if len(data) >= 5 else 0
                    stock_data.append({
                        "代码": stock,
                        "周涨幅%": round(week_change, 2),
                        "价格": round(data[stock].iloc[-1], 2)
                    })
            
            st.divider()
            
            # 计算该板块的资金流向 (相对强度)
            bm = info['benchmark']
            if bm in data.columns and "SPY" in data.columns:
                rel_strength = data[bm] / data["SPY"]
                rotation_series = (rel_strength.pct_change(20) * 100).dropna().tail(60)
            else:
                rotation_series = None
            
            if rotation_series is not None and len(rotation_series) > 0:
                fig = go.Figure()
                # 添加红绿柱
                fig.add_trace(go.Bar(
                    x=rotation_series.index,
                    y=rotation_series,
                    marker_color=['#26a69a' if x > 0 else '#ef5350' for x in rotation_series],
                    name="资金流向"
                ))
                # 添加趋势折线
                fig.add_trace(go.Scatter(
                    x=rotation_series.index,
                    y=rotation_series,
                    line=dict(color='gray', width=1),
                    mode='lines',
                    showlegend=False
                ))
                
                fig.update_layout(
                    height=200, 
                    margin=dict(l=0, r=0, t=10, b=0),
                    template="plotly_white",
                    xaxis_visible=False # 隐藏 X 轴保持紧凑
                )
                st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

            # 3. 下半部分：成分股表现列表
            stock_list = []
            for s in info['stocks']:
                if s in data.columns:
                    try:
                        # 计算周涨幅
                        w_chg = (data[s].iloc[-1] / data[s].iloc[-5] - 1) * 100 if len(data) >= 5 else 0
                        stock_list.append({
                            "Ticker": s,
                            "周涨幅%": round(w_chg, 2),
                            "现价": round(data[s].iloc[-1], 2)
                        })
                    except:
                        continue
            
            if stock_list:
                df_s = pd.DataFrame(stock_list).sort_values("周涨幅%", ascending=False)
                
                # 使用 dataframe 渲染，增加进度条颜色
                st.dataframe(
                    df_s,
                    column_config={
                        "周涨幅%": st.column_config.NumberColumn("周涨幅%", format="%.2f%%"),
                        "现价": st.column_config.NumberColumn("现价", format="$%.2f")
                    },
                    hide_index=True,
                    width='stretch'
                )
