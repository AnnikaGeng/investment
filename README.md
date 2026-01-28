# 📊 投资分析仪表板 (Investment Analysis Dashboard)

一个基于 Streamlit 的多功能投资分析平台，提供实时板块资金流向监控、热门赛道追踪、智能选股推荐和深度 ETF 分析。

A comprehensive Streamlit-based investment analysis platform that provides real-time sector rotation monitoring, hot sector tracking, intelligent stock recommendations, and in-depth ETF analysis.

---

## 🎯 核心功能 (Core Features)

### 1. **板块资金流向监控** (Sector Rotation Monitoring)
- 实时追踪 15 个主要 ETF 板块相对 SPY 的资金流向
- 20 日动能计算与可视化
- 自动排名与排名变动追踪
- 展示各板块主要成分股

### 2. **动态热门赛道分析** (Dynamic Hot Sector Analysis)
- 自动识别表现最强的 Top 10 细分赛道
- 支持多周期分析（5日、10日、20日）
- 50+ 细分赛道覆盖（科技、医疗、能源、金融等）
- 龙头股表现追踪与排名

### 3. **今日推荐股票** (Daily Stock Recommendations)
- **智能评分系统** (160分制):
  - 热门赛道得分 (30分)
  - 均线分析 (50分) - MA30/MA50/MA100
  - 价格行为分析 (50分) - RSI、回调买点识别
  - 基本面分析 (30分) - PE估值、增长指标
- 从热门赛道的成分股中自动筛选 Top 3 推荐
- 识别健康回调买点，避免追高

### 4. **深度 ETF 分析页面** (Deep ETF Analysis)
- 15 个主要 ETF 的独立详细分析页面
- RRG (Relative Rotation Graph) 象限分析
- 相对强度趋势追踪
- 成分股涨跌幅排行与买点识别

---

## 🏗️ 架构设计 (Architecture)

### 技术栈 (Tech Stack)

```
Frontend & Backend: Streamlit (Python)
Data Source:        yfinance API
Data Processing:    pandas
Visualization:      Plotly
Caching:            Streamlit cache_data (24h TTL)
```

### 项目结构 (Project Structure)

```
investment/
│
├── app.py                          # 主页 - 板块资金流向监控
├── requirements.txt                # 项目依赖
├── fetch_etf_holdings.py          # ETF持仓数据获取工具
│
└── pages/                          # Streamlit 多页面应用
    ├── 00_动态热门赛道.py          # 热门赛道动态追踪
    ├── 01_细分赛道分析.py          # Top 10 细分赛道深度分析
    ├── 02_今日推荐股票.py          # 智能选股推荐系统
    │
    └── 04-17_*.py                  # 15个ETF详细分析页面
        ├── 04_XLK_科技.py
        ├── 04_XBI_生物科技.py
        ├── 05_XLE_能源.py
        ├── 06_XLF_金融.py
        ├── 07_XLI_工业.py
        ├── 08_XLV_医疗.py
        ├── 09_XLY_可选消费.py
        ├── 10_XLB_材料.py
        ├── 11_XLP_必选消费.py
        ├── 12_XLU_公用事业.py
        ├── 13_XLRE_房地产.py
        ├── 14_XLC_通信服务.py
        ├── 15_ARKG_基因创新.py
        ├── 16_ARKK_颠覆性创新.py
        └── 17_ARKX_航天太空.py
```

### 数据流架构 (Data Flow Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                      yfinance API                           │
│              (Yahoo Finance Real-time Data)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Caching Layer                         │
│         (@st.cache_data, TTL=24h/1h)                       │
│   • ETF Price Data     • Stock Price Data                  │
│   • Sector Rankings    • Stock Analysis Results            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Analysis & Calculation Layer                  │
│                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │ Sector       │  │ Stock Scoring │  │ RRG Quadrant    │ │
│  │ Rotation     │  │ System        │  │ Analysis        │ │
│  │ Analysis     │  │               │  │                 │ │
│  └──────────────┘  └───────────────┘  └─────────────────┘ │
│                                                             │
│  • Relative Strength Calculation                           │
│  • Moving Average Analysis (MA30/50/100)                   │
│  • RSI & Price Action Detection                            │
│  • Fundamental Scoring (PE, Growth)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Visualization Layer (Plotly)                 │
│                                                             │
│  • Bar Charts (Sector Rotation)                            │
│  • Line Charts (Price Trends)                              │
│  • DataFrames (Stock Rankings)                             │
│  • Metrics Cards (Scores & Indicators)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit UI Layer                             │
│                                                             │
│  Main Page → Multi-page App (18 pages total)               │
│  • Responsive Layout (columns, containers)                 │
│  • Interactive Widgets (radio, selectbox)                  │
│  • Real-time Updates                                       │
└─────────────────────────────────────────────────────────────┘
```

### 核心算法 (Core Algorithms)

#### 1. **相对强度计算** (Relative Strength Calculation)
```python
# 计算 ETF 相对于 SPY 的表现
relative_strength = ETF_price / SPY_price
momentum = (relative_strength.current / relative_strength.20_days_ago - 1) * 100
```

#### 2. **智能选股评分系统** (Smart Stock Scoring System)
```
总分 = 热门赛道得分 + 均线分析得分 + 价格行为得分 + 基本面得分
     (30分)        (50分)         (50分)         (30分)

其中：
- 热门赛道得分: 基于股票在 Top 5 热门赛道中的出现次数
- 均线分析: 多头排列检测 (MA30 > MA50 > MA100)
- 价格行为: RSI健康度 + 回踩买点识别 + 成交量确认
- 基本面: PE估值 + 盈利增长 + 分析师评级
```

#### 3. **RRG 象限分析** (RRG Quadrant Analysis)
```
四个象限:
- Leading (领先): 高相对强度 + 上升趋势
- Weakening (走弱): 高相对强度 + 下降趋势
- Lagging (落后): 低相对强度 + 下降趋势
- Improving (改善): 低相对强度 + 上升趋势
```

---

## 🚀 快速开始 (Quick Start)

### 安装依赖 (Installation)

```bash
# 克隆项目
git clone <repository-url>
cd investment

# 安装依赖
pip install -r requirements.txt
```

### 运行应用 (Run Application)

```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址: `http://localhost:8501`

### 部署到 Streamlit Cloud (Deploy to Streamlit Cloud)

1. 将项目推送到 GitHub
2. 登录 [Streamlit Cloud](https://streamlit.io/cloud)
3. 创建新应用，选择主分支和 `app.py`
4. 等待部署完成

---

## 📊 数据说明 (Data Description)

### 覆盖的板块 (Covered Sectors)

**SPDR Sector ETFs:**
- XLK (Technology) - 科技
- XLE (Energy) - 能源
- XLF (Financials) - 金融
- XLI (Industrial) - 工业
- XLV (Healthcare) - 医疗
- XLY (Consumer Discretionary) - 可选消费
- XLP (Consumer Staples) - 必需消费
- XLB (Materials) - 材料
- XLU (Utilities) - 公用事业
- XLRE (Real Estate) - 房地产
- XLC (Communication Services) - 通信服务

**ARK Innovation ETFs:**
- ARKK (Disruptive Innovation) - 颠覆性创新
- ARKG (Genomic Revolution) - 基因组学
- ARKX (Space Exploration) - 航天太空

**Other Specialized ETFs:**
- XBI (Biotech) - 生物科技
- SMH (Semiconductors) - 半导体
- SOXX (Semiconductor Equipment) - 半导体设备
- IGV (Software) - 软件
- ... 等 50+ 细分赛道

### 数据更新频率 (Data Update Frequency)

- **缓存周期**: 24小时（主要数据）/ 1小时（实时推荐）
- **数据源**: Yahoo Finance API (通过 yfinance)
- **历史数据**: 60天 - 1年（取决于分析类型）

---

## 🎨 特色功能详解 (Feature Highlights)

### 健康回调买点识别 (Healthy Pullback Detection)

系统能够识别以下理想买入场景:
- ✅ RSI 在 40-60 之间（健康区域）
- ✅ 价格回踩 MA30/MA50 附近（±2%）
- ✅ 回调期间成交量缩小（避免恐慌性下跌）
- ✅ 均线保持多头排列
- ❌ 避免追高（远离均线 >10%）
- ❌ 避免超买区域（RSI >80）

### 动态排名系统 (Dynamic Ranking System)

- 自动追踪每日排名变化
- 显示排名升降图标（🚀 上升 / 🔻 下降）
- 支持多周期对比（5日/10日/20日）

---

## ⚙️ 配置说明 (Configuration)

### 缓存调优 (Cache Tuning)

在 `app.py` 和各页面中，可以调整缓存 TTL:

```python
@st.cache_data(ttl=86400)  # 24小时 = 86400秒
def load_data(ticker_list):
    # ...
```

### 添加新的 ETF 板块 (Adding New ETF Sectors)

在 `pages/01_细分赛道分析.py` 中编辑 `SECTOR_ETF_STOCKS`:

```python
SECTOR_ETF_STOCKS = {
    "NEW_ETF": ["STOCK1", "STOCK2", "STOCK3", ...],
    # ...
}

ETF_CHINESE_NAMES = {
    "NEW_ETF": "中文名称",
    # ...
}
```

---

## 🔧 依赖项 (Dependencies)

```
streamlit>=1.28.0      # Web框架
yfinance>=0.2.32       # 金融数据API
pandas>=2.0.0          # 数据处理
plotly>=5.17.0         # 交互式图表
```

---

## 📝 注意事项 (Important Notes)

1. **数据免责声明**: 本工具仅供学习和研究使用，不构成投资建议。投资有风险，决策需谨慎。

2. **数据延迟**: Yahoo Finance 数据可能有 15-20 分钟延迟。

3. **API 限制**: yfinance 有请求频率限制，建议使用缓存避免频繁请求。

4. **股票代码**: 使用美股代码（如 AAPL, TSLA），不支持中国 A 股。

---

## 🤝 贡献 (Contributing)

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证 (License)

MIT License

---

## 👨‍💻 作者 (Author)

Created with ❤️ using Streamlit and Claude Code

**Co-Authored-By:** Claude Sonnet 4.5

---

## 🔗 相关资源 (Resources)

- [Streamlit Documentation](https://docs.streamlit.io/)
- [yfinance Documentation](https://pypi.org/project/yfinance/)
- [Plotly Documentation](https://plotly.com/python/)
- [Relative Rotation Graphs (RRG)](https://www.stockcharts.com/docs/doku.php?id=other-tools:relative-rotation-graphs)
