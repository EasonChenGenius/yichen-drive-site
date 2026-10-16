# v56 证据与重跑

本轮报告：../../business/移动性能与Safari补充验收-v56.md。

## 结果

- performance-summary.json：最终首页5次移动、咨询5次移动、桌面1次；全部原始指标及中位数、最差值。
- browser-results.json：20项主流程、64组布局、12组axe。
- edge-results.json：20项异常与边界交互，49页渲染。
- first-paint-results.json：14项新增首屏／启动／区号／样式失败恢复检查。
- safari-results.json：14项实际桌面Safari原生UI检查；WebDriver超时单独记录。
- safari-mail-queue.json：仅对应虚构Safari咨询，通知留在隔离数据库队列中。

所有账号、电话、称呼及咨询内容均用于隔离QA。原图、未截工具栏的Safari截图和Lighthouse原始JSON位于忽略的output/playwright/perf-v56，不包含生产客户记录。

## 命令

```sh
python3 scripts/build-first-paint.py --check
python tests/serve_qa.py
# 以下在另一个终端，使用已安装的QA专用工具绝对路径：
YICHEN_PLAYWRIGHT_MODULE=/absolute/path/node_modules/playwright \
YICHEN_AXE_PATH=/absolute/path/node_modules/axe-core/axe.min.js \
node tests/test_qa_browser_v54.cjs
YICHEN_PLAYWRIGHT_MODULE=/absolute/path/node_modules/playwright node tests/test_qa_edges_v54.cjs
YICHEN_PLAYWRIGHT_MODULE=/absolute/path/node_modules/playwright node tests/test_first_paint_v56.cjs
YICHEN_LIGHTHOUSE_CLI=/absolute/path/node_modules/lighthouse/cli/index.js python3 tests/performance_v56.py
python tests/test_qa_v54.py
node tests/test_enquiry_ui_v51.cjs
node tests/test_auth_feedback_v52.cjs
```

Lighthouse固定12.8.2，移动默认模拟条件，Chrome冷配置，不能与真实用户INP混用。

Safari使用CUA原生UI，按safari-results.json逐条重跑，不把WebKit测试当作Safari。测试日期若已过，请改为未来同等跨度；5天对应等时刻相差120小时，不是包含首尾日期的天数。

真人参与者待安排（0/5）；iPhone真机、公网、正式条款与经营资料仍未验收。
