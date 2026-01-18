import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import logging

# 抑制 yfinance 的日志
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

# 页面配置
st.set_page_config(layout="wide", page_title="XLB - 材料")

# ETF 信息
ETF_CODE = "XLB"
ETF_NAME = "材料 (Materials)"
ETF_STOCKS = ['LIN', 'NUE', 'SHW', 'APD', 'ECL', 'FCX', 'CLF', 'KIM', 'ALB', 'DOW']
BENCHMARK = "SPY"

st.title(f"📈 {ETF_CODE} - {ETF_NAME}")

# 加载 ETF 数据
@st.cache_data(ttl=86400)
def load_etf_data(etf_code, benchmark):
    """加载 ETF 数据用于计算动能"""
    try:
        # 一次性下载两个ticker
        tickers = f"{etf_code} {benchmark}"
        data = yf.download(tickers, period="1y", progress=False)

        # 处理返回的数据结构
        if isinstance(data.columns, pd.MultiIndex):
            # MultiIndex情况：提取Close列
            close_data = data['Close']
            return close_data
        else:
            # 单一ticker的情况
            return data[['Close']].rename(columns={'Close': etf_code})
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

df_etf = load_etf_data(ETF_CODE, BENCHMARK)

if df_etf is not None and ETF_CODE in df_etf.columns:
    # 计算 20 日动能
    if BENCHMARK in df_etf.columns and len(df_etf[ETF_CODE].dropna()) >= 20:
        rel_strength = df_etf[ETF_CODE] / df_etf[BENCHMARK]
        momentum = rel_strength.pct_change(20, fill_method=None) * 100
        latest_momentum = momentum.iloc[-1]

        # 显示强度指标
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("20日动能", f"{latest_momentum:.2f}%")
        with col2:
            current_price = df_etf[ETF_CODE].iloc[-1]
            st.metric("当前价格", f"${current_price:.2f}")
        with col3:
            month_return = (df_etf[ETF_CODE].iloc[-1] / df_etf[ETF_CODE].iloc[-20] - 1) * 100
            st.metric("月涨幅", f"{month_return:.2f}%")

        st.divider()

        # 绘制 60 天动能图
        try:
            momentum_60d = momentum.tail(60)
            colors = ['#26a69a' if v >= 0 else '#ef5350' for v in momentum_60d]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=momentum_60d.index,
                y=momentum_60d,
                marker_color=colors,
                showlegend=False
            ))
            fig.update_layout(
                title=f"{ETF_CODE} 60日动能走势",
                height=400,
                xaxis_title="日期",
                yaxis_title="动能 (%)",
                template="plotly_white",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"无法加载动能图表: {e}")

    st.divider()

    # RRG (相对轮动图) 分析
    st.subheader(f"{ETF_CODE} RRG 轮动分析")

    # 时间段选择 - 使用radio buttons实现更好的状态管理
    selected_period = st.radio(
        "选择时间段：",
        options=[7, 30, 90, 180],
        format_func=lambda x: f"{x}天",
        horizontal=True,
        index=0,
        key=f"rrg_period_{ETF_CODE}"
    )

    try:
        rs = df_etf[ETF_CODE] / df_etf[BENCHMARK]
        rs_momentum = rs.pct_change(20, fill_method=None) * 100

        # 根据时间段选择采样点数（7-10个点）
        num_points = min(10, max(7, selected_period // 10))

        # 获取最近N天的数据
        total_days = min(selected_period, len(rs))
        step = max(1, total_days // num_points)

        # 采样数据点
        indices = list(range(-total_days, 0, step)) + [-1]  # 确保包含最新的点
        indices = sorted(list(set(indices)))  # 去重并排序

        x_vals = rs_momentum.iloc[indices].values
        y_vals = rs.iloc[indices].values

        # 归一化Y轴
        y_min, y_max = rs.iloc[-max(60, total_days):].min(), rs.iloc[-max(60, total_days):].max()
        y_normalized = ((y_vals - y_min) / (y_max - y_min) * 100) if y_max != y_min else [50] * len(y_vals)

        fig_rrg = go.Figure()

        # 添加平滑轨迹线
        fig_rrg.add_trace(go.Scatter(
            x=x_vals,
            y=y_normalized,
            mode='lines+markers',
            name='轨迹',
            line=dict(color='#1f77b4', width=3, shape='spline', smoothing=1.3),
            marker=dict(size=8, color=y_normalized, colorscale='Viridis', showscale=False,
                       line=dict(width=1, color='white'))
        ))

        # 标注最新点
        fig_rrg.add_trace(go.Scatter(
            x=[x_vals[-1]],
            y=[y_normalized[-1]],
            mode='markers+text',
            name='当前',
            marker=dict(size=16, color='red', symbol='star'),
            text=['NOW'],
            textposition='top center',
            textfont=dict(size=12, color='red', family='Arial Black')
        ))

        # 标注起始点
        period_name = f"{selected_period}天前"
        fig_rrg.add_trace(go.Scatter(
            x=[x_vals[0]],
            y=[y_normalized[0]],
            mode='markers+text',
            name=period_name,
            marker=dict(size=12, color='gray'),
            text=['START'],
            textposition='bottom center',
            textfont=dict(size=11, color='gray')
        ))

        # 添加象限分割线
        fig_rrg.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5, line_width=2)
        fig_rrg.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5, line_width=2)

        # 动态计算坐标轴范围
        x_range = max(x_vals) - min(x_vals)
        x_padding = max(x_range * 0.15, 2)  # 至少2个单位的padding
        x_min_plot = min(x_vals) - x_padding
        x_max_plot = max(x_vals) + x_padding

        # 确保坐标轴包含0点
        x_min_plot = min(x_min_plot, -x_padding)
        x_max_plot = max(x_max_plot, x_padding)

        y_min_val, y_max_val = 0, 100

        # 添加象限背景
        fig_rrg.add_shape(type="rect", x0=0, y0=50, x1=x_max_plot, y1=y_max_val,
                         fillcolor="lightgreen", opacity=0.15, line_width=0, layer="below")
        fig_rrg.add_shape(type="rect", x0=x_min_plot, y0=50, x1=0, y1=y_max_val,
                         fillcolor="lightblue", opacity=0.15, line_width=0, layer="below")
        fig_rrg.add_shape(type="rect", x0=x_min_plot, y0=y_min_val, x1=0, y1=50,
                         fillcolor="lightyellow", opacity=0.25, line_width=0, layer="below")
        fig_rrg.add_shape(type="rect", x0=0, y0=y_min_val, x1=x_max_plot, y1=50,
                         fillcolor="lightcoral", opacity=0.15, line_width=0, layer="below")

        # 象限标签 - 基于实际坐标轴范围计算位置
        # 右侧标签位置（正值区域的中点）
        x_right_label = x_max_plot * 0.5
        # 左侧标签位置（负值区域的中点）
        x_left_label = x_min_plot * 0.5

        fig_rrg.add_annotation(x=x_right_label, y=75, text="<b>Leading</b><br>强势",
                             showarrow=False, font=dict(size=14, color="green"), opacity=0.7)
        fig_rrg.add_annotation(x=x_left_label, y=75, text="<b>Improving</b><br>改善",
                             showarrow=False, font=dict(size=14, color="blue"), opacity=0.7)
        fig_rrg.add_annotation(x=x_left_label, y=25, text="<b>Lagging</b><br>滞后",
                             showarrow=False, font=dict(size=14, color="orange"), opacity=0.7)
        fig_rrg.add_annotation(x=x_right_label, y=25, text="<b>Weakening</b><br>转弱",
                             showarrow=False, font=dict(size=14, color="red"), opacity=0.7)

        # 设置坐标轴范围
        fig_rrg.update_xaxes(range=[x_min_plot, x_max_plot])
        fig_rrg.update_yaxes(range=[y_min_val, y_max_val])

        fig_rrg.update_layout(
            title=f"{ETF_CODE} RRG 轮动图 ({selected_period}天轨迹 - {len(indices)}个采样点)",
            xaxis_title="动量 (Momentum)",
            yaxis_title="相对强度 (Relative Strength)",
            height=500,
            width=700,
            hovermode='closest',
            template="plotly_white",
            showlegend=True,
            font=dict(size=12)
        )

        st.plotly_chart(fig_rrg, use_container_width=True)

        st.info("""
        **RRG 四象限解释：**
        - 🟢 **Leading (强势)**: 相对强势 + 正动量 → 强势继续上升
        - 🔵 **Improving (改善)**: 相对弱势 → 正动量 → 从弱变强
        - 🟠 **Lagging (滞后)**: 相对弱势 + 负动量 → 持续弱势
        - 🔴 **Weakening (转弱)**: 相对强势 → 负动量 → 从强变弱
        """)

    except Exception as e:
        st.warning(f"RRG 分析计算失败: {e}")

    st.divider()

    # 成分股分析
    @st.cache_data(ttl=86400)
    def load_stocks_data(stocks):
        try:
            data = yf.download(stocks, period="1y", progress=False)
            # 处理返回的数据结构
            if isinstance(data.columns, pd.MultiIndex):
                # MultiIndex情况：提取Close列
                return data['Close']
            else:
                # 单一ticker的情况
                return data[['Close']]
        except Exception as e:
            st.warning(f"成分股数据加载失败: {e}")
            import traceback
            st.warning(traceback.format_exc())
            return None

    st.subheader(f"{ETF_CODE} 成分股表现")

    with st.spinner(f"加载 {ETF_CODE} 的成分股数据..."):
        df_stocks = load_stocks_data(ETF_STOCKS)

    if df_stocks is not None and len(df_stocks.columns) > 0:
        stock_details = []

        for stock in ETF_STOCKS:
            if stock not in df_stocks.columns or len(df_stocks[stock].dropna()) < 5:
                continue

            try:
                week_change = (df_stocks[stock].iloc[-1] / df_stocks[stock].iloc[-5] - 1) * 100
                month_change = (df_stocks[stock].iloc[-1] / df_stocks[stock].iloc[-20] - 1) * 100 if len(df_stocks[stock].dropna()) >= 20 else 0
                current_price = df_stocks[stock].iloc[-1]

                # 获取PE数据
                try:
                    ticker_obj = yf.Ticker(stock)
                    info = ticker_obj.info
                    pe_ratio = info.get('trailingPE', None)
                    forward_pe = info.get('forwardPE', None)
                except:
                    pe_ratio = None
                    forward_pe = None

                stock_details.append({
                    "代码": stock,
                    "周涨幅%": round(week_change, 2),
                    "月涨幅%": round(month_change, 2),
                    "当前价格": round(current_price, 2),
                    "PE": round(pe_ratio, 2) if pe_ratio else None,
                    "Forward PE": round(forward_pe, 2) if forward_pe else None
                })
            except:
                continue

        if stock_details:
            stock_df = pd.DataFrame(stock_details).sort_values("周涨幅%", ascending=False)
            st.dataframe(
                stock_df,
                column_config={
                    "周涨幅%": st.column_config.NumberColumn("周涨幅%", format="%.2f%%"),
                    "月涨幅%": st.column_config.NumberColumn("月涨幅%", format="%.2f%%"),
                    "当前价格": st.column_config.NumberColumn("当前价格", format="$%.2f"),
                    "PE": st.column_config.NumberColumn("PE", format="%.2f"),
                    "Forward PE": st.column_config.NumberColumn("Forward PE", format="%.2f")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info(f"成分股数据暂无")
    else:
        st.info(f"未能加载 {ETF_CODE} 的成分股数据")

else:
    st.error("无法加载数据，请检查网络连接")
