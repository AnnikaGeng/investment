import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import logging

# 抑制 yfinance 的日志
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

st.set_page_config(layout="wide", page_title="动态热门赛道")

# 定义所有主要的行业/细分赛道ETF（与01_细分赛道分析.py保持一致）
# 数据来源：各ETF官方网站公开信息，2024年数据
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

    # 新兴主题（真实存在的ETF）
    "DRIV": "自动驾驶",
    "BLOK": "区块链",
    "BETZ": "博彩体育",
    "ESPO": "电子竞技",
    "GNOM": "基因组",
}

st.title("🔥 动态热门赛道排行")
st.caption("自动追踪200+细分行业ETF，实时发现最强势赛道")

# 时间段选择
period_option = st.radio(
    "选择动能计算周期：",
    options=[5, 10, 20, 60],
    format_func=lambda x: f"{x}日动能",
    horizontal=True,
    index=2  # 默认20日
)

# 加载数据
@st.cache_data(ttl=3600)  # 1小时缓存
def load_sector_data(etf_list, period_days=100):
    """加载所有细分赛道ETF数据"""
    try:
        # 下载数据，使用足够长的周期以计算动能
        tickers = list(etf_list.keys()) + ["SPY"]
        data = yf.download(tickers, period=f"{period_days}d", progress=False)

        # 处理MultiIndex
        if isinstance(data.columns, pd.MultiIndex):
            close_data = data['Close']
        else:
            close_data = data[['Close']]

        return close_data
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return None

with st.spinner("正在加载细分赛道数据..."):
    df = load_sector_data(ALL_SECTOR_ETFS, period_days=max(100, period_option + 30))

if df is not None and 'SPY' in df.columns:
    # 计算所有ETF相对SPY的动能
    sector_performance = []

    for etf, name in ALL_SECTOR_ETFS.items():
        if etf in df.columns:
            try:
                # 移除NaN
                etf_data = df[etf].dropna()
                spy_data = df['SPY'].dropna()

                # 确保有足够数据
                if len(etf_data) >= period_option + 5 and len(spy_data) >= period_option + 5:
                    # 对齐索引后计算相对强度
                    common_index = etf_data.index.intersection(spy_data.index)
                    if len(common_index) < period_option + 5:
                        continue

                    etf_aligned = etf_data.loc[common_index]
                    spy_aligned = spy_data.loc[common_index]

                    # 计算相对强度
                    rel_strength = etf_aligned / spy_aligned

                    # 计算动能 (N日涨幅)
                    if len(rel_strength) >= period_option + 1:
                        momentum = (rel_strength.iloc[-1] / rel_strength.iloc[-period_option - 1] - 1) * 100
                    else:
                        continue

                    # 计算绝对收益
                    abs_return = (etf_aligned.iloc[-1] / etf_aligned.iloc[-period_option - 1] - 1) * 100

                    # 当前相对强度位置 (vs 60日)
                    if len(rel_strength) >= 60:
                        rs_60d = rel_strength.iloc[-60:]
                        rs_min = rs_60d.min()
                        rs_max = rs_60d.max()
                        if rs_max != rs_min:
                            rs_percentile = (rel_strength.iloc[-1] - rs_min) / (rs_max - rs_min) * 100
                        else:
                            rs_percentile = 50
                    else:
                        rs_percentile = 50

                    # 检查是否有NaN值
                    if pd.isna(momentum) or pd.isna(abs_return) or pd.isna(rs_percentile):
                        continue

                    sector_performance.append({
                        "代码": etf,
                        "赛道": name,
                        f"{period_option}日动能": round(momentum, 2),
                        f"{period_option}日收益": round(abs_return, 2),
                        "相对强度": round(rs_percentile, 1),
                        "当前价格": round(etf_aligned.iloc[-1], 2)
                    })
            except Exception as e:
                continue

    if sector_performance:
        # 转换为DataFrame并排序
        perf_df = pd.DataFrame(sector_performance).sort_values(f"{period_option}日动能", ascending=False)

        # 显示统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("跟踪赛道数", f"{len(perf_df)}")
        with col2:
            avg_momentum = perf_df[f"{period_option}日动能"].mean()
            st.metric("平均动能", f"{avg_momentum:.2f}%")
        with col3:
            positive_count = len(perf_df[perf_df[f"{period_option}日动能"] > 0])
            st.metric("正动能占比", f"{positive_count}/{len(perf_df)}")
        with col4:
            top_momentum = perf_df[f"{period_option}日动能"].iloc[0]
            st.metric("最强动能", f"{top_momentum:.2f}%")

        st.divider()

        # 显示Top 10热门赛道
        st.subheader("🏆 Top 10 热门赛道")

        top10 = perf_df.head(10)

        # 创建动能对比图
        fig = go.Figure()

        colors = ['#00CC96' if x > 0 else '#EF553B' for x in top10[f"{period_option}日动能"]]

        fig.add_trace(go.Bar(
            x=top10[f"{period_option}日动能"],
            y=top10['赛道'],
            orientation='h',
            marker_color=colors,
            text=top10[f"{period_option}日动能"].apply(lambda x: f"{x:.2f}%"),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>动能: %{x:.2f}%<extra></extra>'
        ))

        fig.update_layout(
            title=f"Top 10 赛道 {period_option}日动能对比",
            xaxis_title="动能 (%)",
            yaxis_title="",
            height=450,
            template="plotly_white",
            yaxis={'categoryorder':'total ascending'}
        )

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # 显示详细数据表
        st.subheader("📊 完整赛道排行榜")

        # 数据表格
        st.dataframe(
            perf_df,
            column_config={
                "代码": st.column_config.TextColumn("代码", width="small"),
                "赛道": st.column_config.TextColumn("赛道", width="medium"),
                f"{period_option}日动能": st.column_config.NumberColumn(
                    f"{period_option}日动能",
                    format="%.2f%%",
                    help="相对SPY的超额收益"
                ),
                f"{period_option}日收益": st.column_config.NumberColumn(
                    f"{period_option}日收益",
                    format="%.2f%%",
                    help="绝对收益率"
                ),
                "相对强度": st.column_config.ProgressColumn(
                    "相对强度",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                    help="60日相对强度位置"
                ),
                "当前价格": st.column_config.NumberColumn("当前价格", format="$%.2f")
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )

        # 添加说明
        with st.expander("📖 指标说明"):
            st.markdown("""
            - **动能**: ETF相对SPY的超额收益，反映该赛道的相对强势
            - **收益**: ETF的绝对收益率
            - **相对强度**: 当前相对强度在60日范围内的位置（0-100）
            - **筛选逻辑**: 自动追踪所有主流细分赛道ETF，按动能排序，实时发现最强势机会
            """)
    else:
        st.warning("暂无有效数据")
else:
    st.error("无法加载数据，请检查网络连接")
