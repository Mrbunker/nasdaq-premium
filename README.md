# Nasdaq Premium · ETF 溢价

16 只场内美股 ETF 的净值、交易价格和折溢价对比工具。覆盖 12 只纳斯达克 100 ETF、1 只纳斯达克科技 ETF 和 3 只标普 500 ETF。

白底蓝灰主题，红涨绿跌；空心柱表示净值涨跌，实心柱表示场内价格涨跌。下排展示两种涨跌幅的差额，回答每期价格变化中有多少来自溢价变化。

## 使用

需要 Python 3.10+。构建网页只使用 Python 标准库：

```sh
python3 scripts/build.py
```

用浏览器打开 `dist/index.html` 即可。数据、脚本和控件样式都内嵌在页面中，支持离线使用；也可将 `dist/` 交给任意静态站点服务。

功能：

- 横向基金 Tabs，支持方向键、Home/End；指数筛选使用 Tom Select。
- 日柱与月柱切换，显示净值涨跌、场内涨跌、溢价贡献及溢价率变化。
- ECharts 图表缩放、拖动浏览与底部区间选择，保持同日双柱紧邻、不同日期分组。
- ＋/− 或滚轮缩放，按住图表拖动平移；Shift+滚轮可横向浏览。重置按钮回到最近数据。
- 悬浮查看对应数值；当前月显示实际统计截止日。
- 网页提供图表浏览，不提供 CSV 下载入口。

## 项目结构

```text
web/       页面模板、交互脚本、图表和主题样式
vendor/    固定版本的前端控件及第三方许可证
config/    16 只基金的代码、名称和指数类别
data/      经过核验的历史数据快照
scripts/   数据获取、计算、验证、网页构建及图表导出
tests/     涨跌计算、缺失值和份额折算的验证
dist/      构建输出（Git 忽略）
.cache/    下载与绘图缓存（Git 忽略）
```

网页构建与 PNG/PDF 导出互相独立，修改页面后只需运行 `scripts/build.py`。缓存、虚拟环境、CSV 中间文件、图片和压缩包都不进入提交。

## 数据口径

**单位净值**使用基金公布的人民币单位净值；**场内价格**使用未复权收盘价。事后折溢价率为：

```text
（同日期场内收盘价 / 同估值日期公布单位净值 − 1）× 100
```

日涨跌均相对上一场内交易日计算。净值缺失时只保留可计算的场内涨跌，不跳到更早日期补算。

月柱取该自然月最后一个净值与价格同日期均可用的交易日，相对紧邻前月的共同日期计算。当前月标记为月内数据；月涨跌不是日涨跌的平均或简单相加。

```text
溢价贡献（百分点） = 场内涨跌幅 − 净值涨跌幅
溢价率变化（百分点） = 本期溢价率 − 前期溢价率
```

这两个指标分别展示。份额折算日、跨越折算的涨跌区间及缺失基准均留空。价格与单位净值变化不等于含分红总回报。

QDII 同日净值包含中国收盘后的海外市场信息，上述比较属于事后口径，不能还原中国收盘时可知的 IOPV 溢价。

快照的采集时间、截止日期、来源 URL、核验差异和缺失说明保存在 `data/history.json`。

## 更新数据

数据采集使用系统 `curl`，无需券商账号或数据 API 密钥：

```sh
python3 scripts/update_data.py
# 或明确指定已结束的中国交易日
python3 scripts/update_data.py --cutoff 2026-11-05
python3 scripts/build.py
```

默认刷新网络数据。已有本地响应缓存时，可用 `--cached` 重放；快照会记录缓存复用状态。更新失败会恢复原快照。

### 每日自动更新

仓库 [Mrbunker/nasdaq-premium](https://github.com/Mrbunker/nasdaq-premium) 的 `.github/workflows/update-data.yml` 每天北京时间 **09:30、18:30** 刷新来源，包括周末，以补齐延迟公布的 QDII 净值。GitHub 定时任务可能延迟，具体新数据仍取决于来源的公布时间。收盘前运行只采集前一个已结束的中国交易日。

更新后依次进行价格交叉核验、日/月涨跌计算和快照验证，全部通过才提交 `data/history.json`；失败保留上次有效快照。也可在 GitHub **Actions → Refresh ETF data → Run workflow** 手动触发，并选择填写截止日期。工作流使用仓库自带的 `GITHUB_TOKEN`，无需保存个人 PAT。仓库需允许 Actions 运行及写入内容。

### Cloudflare Pages

将 Pages 项目连接到 **Mrbunker/nasdaq-premium**，生产分支选 `main`，框架预设选 None：

- 构建命令：`python3 scripts/build.py`
- 构建输出目录：`dist`
- 根目录：留空

开启生产分支自动部署后，数据提交会触发重新构建。网页本身是静态页面，访问时不请求行情 API；已打开的页面需要重新加载才能看到新快照。

来源：

- 天天基金/东方财富单位净值：`fund.eastmoney.com/pingzhongdata/{code}.js`
- 净值条数及最新记录核验：`api.fund.eastmoney.com/f10/lsjz`
- 东方财富未复权收盘价：`push2his.eastmoney.com/api/qt/stock/kline/get`
- 腾讯历史日线交叉核验：`web.ifzq.gtimg.cn/appstock/app/fqkline/get`

## 验证和导出

前端视窗模型测试需要 Node.js 18+；构建网页不需要 Node.js。

```sh
make check
# 没有 make 时
python3 -m unittest discover -s tests -v
node tests/test_chart_viewport.js
node tests/test_chart_options.js
python3 scripts/validate_snapshot.py
python3 scripts/build.py
```

可选 PNG/PDF 导出需要 Matplotlib：

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-charts.txt
.venv/bin/python scripts/render_daily.py
```

图表输出到 `charts/`。中文字体会查找 macOS 的 Arial Unicode 或 Linux 的 Noto Sans CJK；也可通过 `NAQD_FONT_PATH` 指定字体文件。

## 前端依赖

- [Apache ECharts 5.6.0](https://echarts.apache.org)：双柱图、历史概览、双端滑块与滚轮缩放，Apache-2.0。
- [Pico CSS 2.1.1](https://picocss.com)：轻量基础样式，MIT。
- [Tom Select 2.4.3](https://tom-select.js.org)：下拉菜单与键盘交互，Apache-2.0。

依赖已固定版本并保存在 `vendor/`，运行页面时不加载远程 CDN。第三方许可见 `vendor/` 与 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
