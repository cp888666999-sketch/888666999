# 架构说明

## 模块职责

| 模块 | 职责 | 依赖 |
|---|---|---|
| `qslab.quant.indicators` | 纯函数计算 MACD/KDJ/ATR/BOLL | pandas, numpy |
| `qslab.spider.base` | 限速、重试、代理的 HTTP 客户端 | requests |
| `qslab.spider.firecrawl` | Firecrawl 抓取/搜索/站点地图 | requests |
| `qslab.config` | 读取 `.env` 与环境变量 | 标准库 |
| `qslab.cli` | 组合上述模块，提供命令行 | 全部 |

## 数据流

```text
CSV / 数据源
    │
    ▼
qslab.quant.indicators.add_indicators()
    │
    ▼
带 DIF/DEA/MACD/K/D/J/ATR/BOLL 的 DataFrame
    │
    ├─→ CLI 打印
    └─→ 写出 CSV / 后续回测
```

抓取链路：

```text
URL / 查询词
    │
    ▼
FirecrawlClient.scrape / search
    │
    ▼
markdown / 结构化结果 → 本地文件或下游解析
```

## 扩展点

1. **数据源**：在 `qslab/data/` 新增 AkShare/Tushare 适配器，输出统一 OHLCV DataFrame。
2. **策略/回测**：新增 `qslab/backtest/`，输入为 `add_indicators()` 的结果。
3. **爬虫**：优先用 `FirecrawlClient` 处理 JS 渲染页面；简单静态页用 `HttpClient`。
4. **可视化**：新增 `qslab/viz/`，不要污染指标模块。

## 安全与合规

- 指标模块是纯函数，不读文件、不联网。
- API key 只从环境变量/`.env` 读取，`.env` 已被 `.gitignore` 忽略。
- 抓取遵守 robots.txt、网站条款与当地法律；不实现验证码/登录绕过。
