import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="细分赛道分析")

# 定义精细化板块及其核心个股 (还原图片中的细分赛道)
etf_data_map = {
    "Elec-Semiconductor Mfg": {
        "name": "芯片制造/半导体",
        "benchmark": "SMH", # 也可以用基准 ETF
        "stocks": ["TSM", "INTC", "TXN", "ADI", "NXPI", "MCHP", "ON", "GFS"] #
    },
    "Elec-Semiconductor Equip": {
        "name": "芯片设备/光刻机",
        "benchmark": "SOXX",
        "stocks": ["ASML", "LRCX", "AMAT", "KLAC", "TER", "ENTG", "MKSI", "NVMI"] #
    },
    "AeroSpace-New Space": {
        "name": "新航天/卫星技术",
        "benchmark": "ARKX",
        "stocks": ["RKLB", "ASTS", "SATS", "PL", "FLY", "LUNR", "VOYG", "RDW"] #
    },
    "AeroSpace-Traditional": {
        "name": "传统航天/军工",
        "benchmark": "ITA",
        "stocks": ["GE", "RTX", "BA", "LMT", "GD", "NOC", "HWM"] #
    },
    "Mining-Lithium": {
        "name": "锂矿/电池供应链",
        "benchmark": "LIT",
        "stocks": ["ALB", "LAC", "SGML", "SLI", "LAR", "ELVR", "ABAT"] #
    },
    "Mining-Uranium": {
        "name": "铀矿/核能循环",
        "benchmark": "URA",
        "stocks": ["CCJ", "UEC", "NXE", "UUUU", "DNN", "EU"] #
    },
    "Energy-Alt-Storage": {
        "name": "储能/高贝塔电力",
        "benchmark": "ICLN",
        "stocks": ["BE", "QS", "EOSE", "FLNC", "PLUG", "ENVX", "AMRC"] #
    }
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
