# QA证据与重跑方式

仅使用隔离QA服务，禁止将浏览器测试指向真实客户服务。固定端口127.0.0.1:8767，外部网络在浏览器用例中被阻止。

## 工具

- 后端：现有requirements-production.txt；测试不启动邮件线程。
- 浏览器：Playwright（本机缓存工具）；axe-core 4.10.3；Lighthouse 12.8.2。
- 所有截图中的客户和后台资料均为虚构QA数据。
- browser-results.json：20项主交互、64组布局、12组axe。
- edge-results.json：20项补充交互和49个页面。
- performance-summary.json：3个最终本地实验室用例；原始Lighthouse报告在忽略的output/playwright/qa-v54中。
- security-scan.json：静态模式扫描，不是完整渗透测试。

## 后端重跑

```sh
python tests/test_enquiry_v51.py
python tests/test_accounts_v52.py
python tests/test_qa_v54.py
node tests/test_enquiry_ui_v51.cjs
node tests/test_auth_feedback_v52.cjs
```

Python必须使用装有requirements-production.txt的环境。

## 浏览器重跑

```sh
python tests/serve_qa.py
# 另一个终端，使用已有独立安装的测试工具，不向生产依赖添加浏览器：
YICHEN_PLAYWRIGHT_MODULE=/absolute/path/node_modules/playwright \
YICHEN_AXE_PATH=/absolute/path/node_modules/axe-core/axe.min.js \
node tests/test_qa_browser_v54.cjs
YICHEN_PLAYWRIGHT_MODULE=/absolute/path/node_modules/playwright \
node tests/test_qa_edges_v54.cjs
```

黄金场景采用2026-10-16—21及20—23的验收日期；在这些日期之后重跑，请先将浏览器黄金场景改为未来日期，保留同样的5天／3天跨度。新增API边界测试主案例使用相对未来日期；原v51历史测试仍保留当次指定日期。

## 限制

真实域名、备案、生产HTTPS、真实邮件收件、远端RLS、Safari／iPhone真机、完整人工无障碍、真实用户INP及5位真实用户测试均不能由这些本地报告代替。

## 流程截图

- [搜索与筛选](search-desktop.jpg)
- [咨询表与5天租期](enquiry-desktop.jpg)
- [提交成功回执](enquiry-success.jpg)
- [账户中的真实需求](my-inquiries.jpg)
- [手机咨询表](enquiry-mobile.jpg)
- [后台完成状态](operator-completed.jpg)

原图和确认封面保持不变；图片压缩只用于发布副本。
