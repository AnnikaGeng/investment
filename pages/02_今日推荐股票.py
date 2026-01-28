import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import logging
from datetime import datetime, timedelta

# 抑制 yfinance 的日志
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

st.set_page_config(layout="wide", page_title="今日推荐股票")

st.title("🎯 今日推荐股票")
st.caption("基于热门赛道、均线分析、价格行为和基本面的综合评分")

# 定义所有主要的行业/细分赛道ETF
ALL_SECTOR_ETFS = {
    # 科技细分
    "XLK": "科技整体",
    "SMH": "半导体",
    "SOXX": "半导体设备",
    "IGV": "软件",
    "CLOU": "云计算",
    "HACK": "网络安全",
    "FINX": "金融科技",
    "BOTZ": "机器人自动化",
    "ROBO": "机器人AI",

    # ARK系列
    "ARKK": "颠覆性创新",
    "ARKG": "基因组学",
    "ARKX": "太空探索",

    # 医疗细分
    "XLV": "医疗整体",
    "XBI": "生物科技",
    "IBB": "生物技术",
    "IHI": "医疗设备",
    "XPH": "制药",

    # 能源细分
    "XLE": "能源整体",
    "XOP": "石油勘探",
    "ICLN": "清洁能源",
    "TAN": "太阳能",
    "LIT": "锂电池",
    "URA": "铀矿核能",
    "ACES": "清洁能源存储",

    # 金融细分
    "XLF": "金融整体",
    "KRE": "地区银行",
    "IAI": "券商投行",
    "KIE": "保险",

    # 工业细分
    "XLI": "工业整体",
    "ITA": "航空航天国防",
    "PAVE": "基建",
    "IYT": "运输",

    # 消费细分
    "XLY": "可选消费",
    "XLP": "必需消费",
    "XRT": "零售",
    "AWAY": "旅游酒店",
    "GAMR": "游戏电竞",

    # 房地产细分
    "XLRE": "房地产整体",
    "VNQ": "REITs",
    "INDS": "工业地产",

    # 通信材料公用
    "XLC": "通信服务",
    "SOCL": "社交媒体",
    "XLB": "材料整体",
    "PICK": "矿业金属",
    "COPX": "铜矿",
    "XLU": "公用事业",

    # 新兴主题
    "DRIV": "自动驾驶",
    "BLOK": "区块链",
    "BETZ": "博彩体育",
    "ESPO": "电子竞技",
    "GNOM": "基因组",
}

# ETF持仓数据
ETF_HOLDINGS = {
    "XLK": ["AAPL", "NVDA", "MSFT", "AVGO", "CRM", "ORCL", "CSCO", "AMD", "ACN", "ADBE"],
    "SMH": ["TSM", "NVDA", "ASML", "AMD", "INTC", "QCOM", "AVGO", "TXN", "AMAT", "MU"],
    "SOXX": ["NVDA", "AVGO", "AMD", "QCOM", "TXN", "INTC", "ADI", "AMAT", "LRCX", "KLAC"],
    "IGV": ["MSFT", "ORCL", "CRM", "ADBE", "INTU", "NOW", "PLTR", "SNOW", "TEAM", "WDAY"],
    "XLV": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "AMGN", "DHR", "PFE"],
    "XBI": ["VRTX", "REGN", "ALNY", "BMRN", "SRPT", "IONS", "EXEL", "UTHR", "ARWR", "NBIX"],
    "XLE": ["XOM", "CVX", "COP", "EOG", "SLB", "PXD", "MPC", "PSX", "VLO", "OXY"],
    "XLF": ["BRK.B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK"],
    "XLI": ["GE", "CAT", "RTX", "UNP", "HON", "UPS", "BA", "DE", "LMT", "ADP"],
    "DRIV": ["TSLA", "NIO", "RIVN", "LCID", "GM", "F", "ALB", "APTV", "ON", "MBLY"],
    "ARKK": ["TSLA", "COIN", "ROKU", "RBLX", "SHOP", "HOOD", "PATH", "ZM", "CRSP", "TDOC"],
    "XLY": ["AMZN", "TSLA", "BABA", "MCD", "SBUX", "NFLX", "NKE", "HD", "LOW", "RCL"],
    "XLP": ["PG", "KO", "MO", "KR", "WMT", "GIS", "CAG", "ADM", "CLX", "UL"],
    "XLU": ["NEE", "DUK", "SO", "D", "AES", "DTE", "EXC", "EIX", "ED", "NRG"],
    "XLRE": ["AMT", "PLD", "EQIX", "DLR", "WELL", "AVB", "SPG", "ARE", "EQR", "UMH"],
    "XLC": ["META", "GOOGL", "GOOG", "VZ", "T", "CMCSA", "CHTR", "NXST", "LYV", "ATVI"],
    "ARKG": ["CRSP", "TDOC", "EDIT", "VEEV", "GILD", "SDGR", "SQ", "BEAM", "ZM", "VCYT"],
    "ARKX": ["RKLB", "LMT", "AVAV", "IRDM", "NOC", "RTX", "VSAT", "SPCE", "AXL", "MAXR"],
    "CLOU": ["MSFT", "ORCL", "AMZN", "CRM", "SNOW", "DDOG", "NET", "TEAM", "ZM", "SHOP"],
    "HACK": ["CRWD", "PANW", "ZS", "FTNT", "OKTA", "NET", "CYBR", "S", "TENB", "RPD"],
    "FINX": ["SQ", "PYPL", "V", "MA", "COIN", "SOFI", "AFRM", "HOOD", "NU", "UPST"],
    "BOTZ": ["NVDA", "ISRG", "ABB", "FANUC", "ROK", "TER", "ZBRA", "EMR", "CGNX", "IRBT"],
    "ROBO": ["NVDA", "ISRG", "INTC", "SMC", "ABB", "FANUC", "ROK", "TER", "KEYENCE", "EMR"],
    "IBB": ["AMGN", "GILD", "VRTX", "REGN", "BIIB", "MRNA", "ALNY", "SGEN", "BMRN", "INCY"],
    "IHI": ["ISRG", "TMO", "ABT", "DHR", "SYK", "BSX", "EW", "IDXX", "ZBH", "BAX"],
    "XPH": ["LLY", "JNJ", "ABBV", "MRK", "PFE", "BMY", "AMGN", "GILD", "REGN", "BIIB"],
    "ICLN": ["ENPH", "FSLR", "SEDG", "NEE", "PLUG", "ON", "ALB", "RUN", "TSLA", "BEP"],
    "TAN": ["ENPH", "FSLR", "SEDG", "RUN", "CSIQ", "JKS", "DQ", "MAXN", "NOVA", "ARRY"],
    "LIT": ["ALB", "SQM", "LTHM", "LAC", "PLL", "SGML", "TSLA", "PANASONIC", "LG", "CATL"],
    "URA": ["CCJ", "KAP", "UUUU", "DNN", "EU", "UEC", "URG", "PALADIN", "PENINSULA", "NXE"],
    "ACES": ["ENPH", "SEDG", "PLUG", "BE", "FCEL", "BLNK", "CHPT", "FLR", "TSLA", "ALB"],
    "KRE": ["HBAN", "RF", "KEY", "CFG", "FITB", "MTB", "EWBC", "ZION", "SNV", "WBS"],
    "IAI": ["MS", "GS", "SCHW", "BLK", "SPGI", "MCO", "CME", "ICE", "MSCI", "NDAQ"],
    "KIE": ["PGR", "CB", "TRV", "ALL", "MET", "PRU", "AIG", "AFL", "HIG", "AJG"],
    "ITA": ["RTX", "LMT", "BA", "GD", "NOC", "TXT", "LHX", "HWM", "AXON", "WWD"],
    "PAVE": ["CAT", "URI", "VMC", "MLM", "EME", "FTV", "PWR", "BLDR", "MTZ", "SUM"],
    "IYT": ["UNP", "UPS", "FDX", "NSC", "CSX", "UAL", "DAL", "AAL", "LUV", "JBHT"],
    "XRT": ["CVNA", "CHWY", "ETSY", "W", "BABA", "DDS", "BBWI", "DKS", "RVLV", "FL"],
    "AWAY": ["MAR", "HLT", "H", "RCL", "CCL", "NCLH", "EXPE", "BKNG", "ABNB", "TCOM"],
    "GAMR": ["RBLX", "EA", "TTWO", "NTES", "BILI", "HUYA", "SE", "PLTK", "DKNG", "U"],
    "VNQ": ["AMT", "PLD", "EQIX", "PSA", "WELL", "DLR", "O", "SPG", "AVB", "EQR"],
    "INDS": ["PLD", "DRE", "FR", "REXR", "EGP", "STAG", "TRNO", "ILPT", "NSA", "PSB"],
    "SOCL": ["META", "SNAP", "PINS", "MTCH", "BMBL", "RDDT", "ZG", "YELP", "ANGI", "IAC"],
    "XLB": ["LIN", "APD", "SHW", "ECL", "NUE", "DD", "ALB", "FCX", "NEM", "DOW"],
    "PICK": ["RIO", "BHP", "VALE", "FCX", "SCCO", "TECK", "FM", "NEM", "GOLD", "HL"],
    "COPX": ["FCX", "SCCO", "TECK", "FM", "CMCL", "HBM", "TGB", "COPX", "CDE", "HL"],
    "BLOK": ["COIN", "MSTR", "RIOT", "MARA", "CLSK", "HIVE", "HUT", "BITF", "CORZ", "CIFR"],
    "BETZ": ["DKNG", "FLT", "CHDN", "PENN", "CZR", "MGM", "WYNN", "LVS", "GNOG", "BALY"],
    "ESPO": ["RBLX", "EA", "TTWO", "NTES", "GME", "BILI", "SE", "AMD", "NVDA", "ATVI"],
    "GNOM": ["ILMN", "TDOC", "EXACT", "NTRA", "PACB", "IONS", "CRSP", "EDIT", "NTLA", "BEAM"],
}

# 加载数据
@st.cache_data(ttl=3600)
def load_sector_data(etf_list, period_days=100):
    """加载所有细分赛道ETF数据"""
    try:
        tickers = list(etf_list.keys()) + ["SPY"]
        data = yf.download(tickers, period=f"{period_days}d", progress=False)

        if isinstance(data.columns, pd.MultiIndex):
            close_data = data['Close']
        else:
            close_data = data[['Close']]

        return close_data
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return None

@st.cache_data(ttl=3600)
def load_stock_data(stock_list, period="1y"):
    """加载股票数据 - 使用1年数据以支持MA100计算"""
    try:
        data = yf.download(stock_list, period=period, progress=False)
        return data
    except Exception as e:
        st.error(f"股票数据加载失败: {e}")
        return None

def calculate_moving_average_score(stock_data, ticker):
    """计算均线分析得分 - 使用MA30/MA50/MA100"""
    try:
        if isinstance(stock_data['Close'].columns, pd.Index) and ticker in stock_data['Close'].columns:
            close_prices = stock_data['Close'][ticker].dropna()
        else:
            close_prices = stock_data['Close'].dropna()

        if len(close_prices) < 100:
            return 0, "数据不足"

        current_price = close_prices.iloc[-1]
        ma30 = close_prices.iloc[-30:].mean()
        ma50 = close_prices.iloc[-50:].mean()
        ma100 = close_prices.iloc[-100:].mean()

        score = 0
        signals = []

        # 价格在所有均线上方 (30分)
        if current_price > ma30 and current_price > ma50 and current_price > ma100:
            score += 30
            signals.append("多头排列")
        elif current_price > ma30 and current_price > ma50:
            score += 20
            signals.append("短期强势")
        elif current_price > ma30:
            score += 10
            signals.append("突破MA30")

        # 均线多头排列 (20分)
        if ma30 > ma50 > ma100:
            score += 20
            signals.append("均线多头")
        elif ma30 > ma50:
            score += 10

        return score, ", ".join(signals) if signals else "中性"
    except Exception as e:
        return 0, f"计算错误: {str(e)}"

def calculate_price_action_score(stock_data, ticker):
    """计算价格行为得分 - 识别健康回调买点"""
    try:
        if isinstance(stock_data['Close'].columns, pd.Index) and ticker in stock_data['Close'].columns:
            close_prices = stock_data['Close'][ticker].dropna()
            volume_data = stock_data['Volume'][ticker].dropna() if 'Volume' in stock_data else None
        else:
            close_prices = stock_data['Close'].dropna()
            volume_data = stock_data['Volume'].dropna() if 'Volume' in stock_data else None

        if len(close_prices) < 100:
            return 0, "数据不足"

        current_price = close_prices.iloc[-1]
        score = 0
        signals = []

        # 1. RSI分析 (15分) - 避免超买区域
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        rsi = calculate_rsi(close_prices)
        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

        if 40 <= current_rsi <= 60:
            score += 15
            signals.append(f"RSI健康 {current_rsi:.1f}")
        elif 30 <= current_rsi < 40 or 60 < current_rsi <= 70:
            score += 10
            signals.append(f"RSI可接受 {current_rsi:.1f}")
        elif current_rsi > 80:
            score += 0
            signals.append(f"RSI超买 {current_rsi:.1f} ⚠️")
        elif current_rsi < 30:
            score += 5
            signals.append(f"RSI超卖 {current_rsi:.1f}")

        # 2. 距离均线分析 (20分) - 寻找回踩买点
        ma30 = close_prices.iloc[-30:].mean()
        ma50 = close_prices.iloc[-50:].mean()

        dist_to_ma30 = ((current_price - ma30) / ma30) * 100
        dist_to_ma50 = ((current_price - ma50) / ma50) * 100

        # 接近MA30 (±2%)
        if -2 <= dist_to_ma30 <= 2:
            score += 20
            signals.append(f"回踩MA30 {dist_to_ma30:+.1f}%")
        # 接近MA50 (±2-5%)
        elif -5 <= dist_to_ma50 <= 5:
            score += 15
            signals.append(f"回踩MA50 {dist_to_ma50:+.1f}%")
        # 远离均线 (>10%) - 不追高
        elif dist_to_ma30 > 10 or dist_to_ma50 > 10:
            score += 0
            signals.append(f"远离均线 ⚠️")
        # 在均线之间
        elif 2 < dist_to_ma30 <= 10:
            score += 10
            signals.append(f"MA30上方 {dist_to_ma30:+.1f}%")

        # 3. 短期走势 (10分) - 避免急涨
        momentum_5d = (close_prices.iloc[-1] / close_prices.iloc[-5] - 1) * 100

        if 0 <= momentum_5d <= 3:
            score += 10
            signals.append(f"温和上涨 {momentum_5d:+.1f}%")
        elif -3 <= momentum_5d < 0:
            score += 8
            signals.append(f"健康回调 {momentum_5d:+.1f}%")
        elif momentum_5d > 5:
            score += 5
            signals.append(f"涨幅过大 {momentum_5d:+.1f}% ⚠️")
        elif 3 < momentum_5d <= 5:
            score += 7
            signals.append(f"较强上涨 {momentum_5d:+.1f}%")

        # 4. 成交量分析 (5分) - 回调缩量为佳
        if volume_data is not None and len(volume_data) >= 20:
            avg_volume_20 = volume_data.iloc[-20:-5].mean()
            recent_volume = volume_data.iloc[-5:].mean()

            volume_change = (recent_volume / avg_volume_20 - 1) * 100

            # 回调期间成交量减少 (理想)
            if -20 <= volume_change <= 0 and momentum_5d < 0:
                score += 5
                signals.append("回调缩量 ✓")
            # 上涨期间成交量温和放大
            elif 0 < volume_change <= 30 and momentum_5d > 0:
                score += 3
                signals.append("量价配合")
            # 成交量异常放大
            elif volume_change > 50:
                score += 0
                signals.append("成交量异常 ⚠️")

        return score, ", ".join(signals) if signals else "中性"
    except Exception as e:
        return 0, f"计算错误: {str(e)}"

def calculate_fundamental_score(ticker):
    """计算基本面得分"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        score = 0
        signals = []

        # PE估值 (15分)
        pe = info.get('trailingPE')
        forward_pe = info.get('forwardPE')

        if forward_pe and forward_pe > 0:
            if forward_pe < 15:
                score += 15
                signals.append(f"低估值PE:{forward_pe:.1f}")
            elif forward_pe < 25:
                score += 10
                signals.append(f"合理估值PE:{forward_pe:.1f}")
            elif forward_pe < 40:
                score += 5
        elif pe and pe > 0:
            if pe < 20:
                score += 15
                signals.append(f"低PE:{pe:.1f}")
            elif pe < 30:
                score += 10
            elif pe < 50:
                score += 5

        # 增长指标 (10分)
        earnings_growth = info.get('earningsQuarterlyGrowth')
        revenue_growth = info.get('revenueGrowth')

        if earnings_growth and earnings_growth > 0.2:
            score += 5
            signals.append(f"盈利增长{earnings_growth*100:.0f}%")

        if revenue_growth and revenue_growth > 0.15:
            score += 5
            signals.append(f"营收增长{revenue_growth*100:.0f}%")

        # 分析师评级 (5分)
        recommendation = info.get('recommendationKey')
        if recommendation in ['strong_buy', 'buy']:
            score += 5
            signals.append("分析师推荐买入")
        elif recommendation == 'hold':
            score += 2

        return score, ", ".join(signals) if signals else "数据不足"
    except Exception as e:
        return 0, "无基本面数据"

# 主流程
with st.spinner("正在分析热门赛道..."):
    df_sectors = load_sector_data(ALL_SECTOR_ETFS, period_days=100)

if df_sectors is not None and 'SPY' in df_sectors.columns:
    # 找出Top 5热门赛道
    sector_momentum = []
    period_option = 20

    for etf, name in ALL_SECTOR_ETFS.items():
        if etf in df_sectors.columns:
            try:
                etf_data = df_sectors[etf].dropna()
                spy_data = df_sectors['SPY'].dropna()

                if len(etf_data) >= period_option + 5 and len(spy_data) >= period_option + 5:
                    common_index = etf_data.index.intersection(spy_data.index)
                    if len(common_index) < period_option + 5:
                        continue

                    etf_aligned = etf_data.loc[common_index]
                    spy_aligned = spy_data.loc[common_index]
                    rel_strength = etf_aligned / spy_aligned

                    if len(rel_strength) >= period_option + 1:
                        momentum = (rel_strength.iloc[-1] / rel_strength.iloc[-period_option - 1] - 1) * 100
                    else:
                        continue

                    if not pd.isna(momentum):
                        sector_momentum.append({
                            'etf': etf,
                            'name': name,
                            'momentum': momentum
                        })
            except:
                continue

    # 排序取Top 5
    sector_momentum.sort(key=lambda x: x['momentum'], reverse=True)
    top5_sectors = sector_momentum[:5]

    st.subheader("🔥 Top 5 热门赛道")

    cols = st.columns(5)
    for i, sector in enumerate(top5_sectors):
        with cols[i]:
            st.metric(
                sector['name'],
                f"{sector['momentum']:.2f}%",
                delta=sector['etf']
            )

    st.divider()

    # 收集Top 5赛道的所有成分股
    all_stocks = set()
    for sector in top5_sectors:
        etf_code = sector['etf']
        if etf_code in ETF_HOLDINGS:
            all_stocks.update(ETF_HOLDINGS[etf_code])

    all_stocks = list(all_stocks)

    if not all_stocks:
        st.warning("未找到热门赛道的成分股数据，请稍后重试")
    else:
        st.subheader(f"📊 正在分析 {len(all_stocks)} 支候选股票...")

        # 加载股票数据 - 使用1年数据支持MA100计算
        with st.spinner("加载股票数据..."):
            stock_data = load_stock_data(all_stocks, period="1y")

        if stock_data is not None:
            # 分析每支股票
            stock_scores = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, ticker in enumerate(all_stocks):
                try:
                    status_text.text(f"分析中: {ticker} ({idx+1}/{len(all_stocks)})")

                    # 热门赛道得分 (30分)
                    sector_score = 0
                    in_sectors = []
                    for sector in top5_sectors:
                        if sector['etf'] in ETF_HOLDINGS and ticker in ETF_HOLDINGS[sector['etf']]:
                            in_sectors.append(sector['name'])

                    if len(in_sectors) >= 3:
                        sector_score = 30
                    elif len(in_sectors) == 2:
                        sector_score = 20
                    elif len(in_sectors) == 1:
                        sector_score = 10

                    # 均线分析 (50分)
                    ma_score, ma_signal = calculate_moving_average_score(stock_data, ticker)

                    # 价格行为 (50分)
                    price_score, price_signal = calculate_price_action_score(stock_data, ticker)

                    # 基本面 (30分)
                    fundamental_score, fundamental_signal = calculate_fundamental_score(ticker)

                    # 总分
                    total_score = sector_score + ma_score + price_score + fundamental_score

                    if total_score > 0:
                        stock_scores.append({
                            '股票代码': ticker,
                            '总分': total_score,
                            '热门赛道': sector_score,
                            '赛道': ", ".join(in_sectors[:2]) if in_sectors else "-",
                            '均线分析': ma_score,
                            '均线信号': ma_signal,
                            '价格行为': price_score,
                            '行为信号': price_signal,
                            '基本面': fundamental_score,
                            '基本面信号': fundamental_signal
                        })

                    progress_bar.progress((idx + 1) / len(all_stocks))
                except Exception as e:
                    continue

            progress_bar.empty()
            status_text.empty()

            if stock_scores:
                # 排序
                stock_scores.sort(key=lambda x: x['总分'], reverse=True)
                top3_stocks = stock_scores[:3]

                st.success(f"✅ 分析完成！从 {len(all_stocks)} 支候选股票中筛选出 Top 3")

                st.divider()

                # 显示Top 3推荐
                st.subheader("🏆 今日推荐 Top 3 股票")

                for rank, stock in enumerate(top3_stocks, 1):
                    with st.container():
                        st.markdown(f"### {rank}. {stock['股票代码']} - 综合评分: {stock['总分']}/160")

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("热门赛道", f"{stock['热门赛道']}/30")
                            st.caption(stock['赛道'])

                        with col2:
                            st.metric("均线分析", f"{stock['均线分析']}/50")
                            st.caption(stock['均线信号'])

                        with col3:
                            st.metric("价格行为", f"{stock['价格行为']}/50")
                            st.caption(stock['行为信号'])

                        with col4:
                            st.metric("基本面", f"{stock['基本面']}/30")
                            st.caption(stock['基本面信号'])

                        st.divider()

                # 显示完整排行榜
                with st.expander("📋 查看完整排行榜"):
                    df_scores = pd.DataFrame(stock_scores)
                    st.dataframe(
                        df_scores,
                        column_config={
                            "股票代码": st.column_config.TextColumn("股票代码", width="small"),
                            "总分": st.column_config.ProgressColumn("总分", format="%d/160", min_value=0, max_value=160),
                            "热门赛道": st.column_config.ProgressColumn("热门赛道", format="%d/30", min_value=0, max_value=30),
                            "赛道": st.column_config.TextColumn("赛道", width="medium"),
                            "均线分析": st.column_config.ProgressColumn("均线", format="%d/50", min_value=0, max_value=50),
                            "均线信号": st.column_config.TextColumn("均线信号", width="medium"),
                            "价格行为": st.column_config.ProgressColumn("价格", format="%d/50", min_value=0, max_value=50),
                            "行为信号": st.column_config.TextColumn("行为信号", width="medium"),
                            "基本面": st.column_config.ProgressColumn("基本面", format="%d/30", min_value=0, max_value=30),
                            "基本面信号": st.column_config.TextColumn("基本面信号", width="medium")
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=600
                    )

                # 评分说明
                with st.expander("📖 评分规则说明"):
                    st.markdown("""
                    **总分: 160分**

                    1. **热门赛道 (30分)**
                       - 出现在3个以上Top5赛道: 30分
                       - 出现在2个Top5赛道: 20分
                       - 出现在1个Top5赛道: 10分

                    2. **均线分析 (50分)**
                       - 价格在所有均线上方 (多头排列): 30分
                       - 均线多头排列 (MA30 > MA50 > MA100): 20分
                       - 部分满足条件: 10-20分

                    3. **价格行为 (50分)**
                       - 20日动能 (>10%: 25分, >5%: 15分, >0%: 5分)
                       - 相对强度位置 (60日内位置 >80%: 15分)
                       - 成交量放大确认: 10分

                    4. **基本面 (30分)**
                       - PE估值合理 (Forward PE <15: 15分, <25: 10分)
                       - 盈利增长 >20%: 5分
                       - 营收增长 >15%: 5分
                       - 分析师推荐买入: 5分

                    **注意**: 本推荐仅供参考，投资有风险，请谨慎决策。
                    """)
            else:
                st.warning("未找到符合条件的股票")
        else:
            st.error("无法加载股票数据")
else:
    st.error("无法加载赛道数据，请检查网络连接")
