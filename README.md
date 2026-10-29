# 888666999 · qslab

量化指标 + 合规爬虫的 Python 工具箱骨架。

## 特性

- **中国软件习惯的指标口径**
  - MACD 柱 = `2 × (DIF - DEA)`
  - KDJ 初值 `K = D = 50`
  - ATR 使用 Wilder RMA
  - BOLL 使用总体标准差 `ddof=0`，包含未完成 K 线
- 一个默认限速、可重试的 HTTP 客户端（不做验证码/反爬绕过）
- CLI：`qslab demo`、`qslab indicators --csv ...`
- pytest + ruff + GitHub Actions

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"

qslab demo
qslab indicators --csv your_ohlc.csv --out with_indicators.csv
pytest -q
```

不安装也可以直接跑演示：

```powershell
python scripts\demo_indicators.py
```

## 目录结构

```text
src/qslab/
  cli.py              命令行入口
  config.py           环境变量配置（不存密钥）
  quant/indicators.py MACD / KDJ / ATR / BOLL
  spider/base.py      限速、重试、代理的 HTTP 客户端
tests/                指标单元测试
scripts/              可直接运行的示例
docs/                 架构说明
```

## 网页抓取（Firecrawl，可选）

`qslab` 内置一个轻量 Firecrawl 客户端，适合抓取需要 JS 渲染的页面，
或直接做网页搜索。没有 key 时指标功能完全不受影响。

```powershell
Copy-Item .env.example .env
# 编辑 .env，填入 FIRECRAWL_API_KEY=fc-...
```

```powershell
# 抓单个页面，输出 markdown
qslab scrape --url https://example.com

# 保存到文件
qslab scrape --url https://example.com --out page.md

# 网页搜索
qslab search --query "order flow footprint chart" --limit 5
```

也可以在自己的代码里调用：

```python
from qslab.spider import FirecrawlClient

client = FirecrawlClient()            # 读取 FIRECRAWL_API_KEY
page = client.scrape("https://example.com")
print((page.get("data") or {}).get("markdown", "")[:500])
```

> key 只从环境变量或 `.env` 读取；`.env` 已在 `.gitignore` 中，不要提交真实密钥。

## 输入格式

`qslab indicators` 读取 CSV，至少包含：

```text
high,low,close
```

输出新增列：

```text
DIF,DEA,MACD,K,D,J,ATR,BOLL_MID,BOLL_UPPER,BOLL_LOWER
```

## 合规边界

本项目只用于**遵守 robots.txt、网站条款和当地法律**的数据采集。
不要用它绕过登录、验证码、付费墙或访问控制。

## Roadmap

- [ ] 数据源适配（AkShare / Tushare，按需）
- [ ] 简单回测框架
- [ ] 指标可视化
- [ ] 定时任务与告警

## License

未指定。需要开源协议时可加 MIT 或 Apache-2.0。
