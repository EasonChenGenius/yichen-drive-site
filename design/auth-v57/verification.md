# 邮箱验证与找回验收证据

55项后端、17项新账户浏览器检查通过；真实邮件发送数量为0。

- api-results.json：归属、重设、限流、异步假SMTP、会话与传输检查。
- ui-results.json：新账户流程、网络错误、移动布局和两页axe。
- core-results.json：20项主流程、64组布局、12组axe。
- edge-results.json：20项异常交互、49页渲染。
- first-paint-results.json：14项首屏与资源失败恢复。
- JPG：仅虚构QA邮箱和已使用的测试验证码，密码保持隐藏。

浏览器只访问127.0.0.1:8767，测试服务关闭真实SMTP。假邮箱与时钟接口只存在于tests/serve_qa.py，生产不存在。

```sh
# Python使用现有requirements-production.txt环境；QA浏览器工具单独安装：
python tests/serve_qa.py
YICHEN_PLAYWRIGHT_MODULE=/absolute/path/node_modules/playwright \
YICHEN_AXE_PATH=/absolute/path/node_modules/axe-core/axe.min.js \
node tests/test_account_email_ui_v57.cjs
```

生产发信、WorkBuddy账号库持久化、HTTPS配置及重启恢复未在本轮完成。新增账户页未重新做Safari或iPhone真机验收。补充说明见../../business/邮箱验证与找回密码-v57.md。
