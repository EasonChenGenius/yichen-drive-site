# Codex 协作说明

> 这份文档用于把 2026-10-13 的工作交接给 Codex。
> **用法**：把下面第一节的提示词整段复制，贴给 Codex 即可；后面几节是给 Codex 查阅的事实与约定。

---

## 一、可以直接复制给 Codex 的提示词

```text
这个项目已经纳入 Git 版本管理，请你在修改代码时遵守以下约定。

项目目录：/Users/eason/Documents/Codex/2026-10-04/xia/outputs/yichen-drive-site
（dist/ 保留源码，没有 src/、没有 package.json。v56起修改JS、公共CSS或首屏模板后，必须运行 python3 scripts/build-first-paint.py 更新发布入口；使用 --check 验证一致，再刷新页面。）

【版本留痕 —— 每次改完必须做】
这个目录是 Git 仓库，远端私有仓库：git@github.com:EasonChenGenius/yichen-drive-site
（对应 https://github.com/EasonChenGenius/yichen-drive-site）

改完代码后请提交一个版本：
    git add -A
    git commit -m "一句话说明改了什么、为什么改"
    git push origin main

提交说明要具体，例如：
  好：填写考斯特与 GL8 的核定座位与年款，来源为行驶证照片
  差：更新车辆资料

重要节点（上线、大改版、资料批量更新）再打标签：
    git tag -a v50 -m "版本说明"
    git push origin v50

【推送必须用 SSH，不要用 HTTPS】
这台机器到 github.com 的 443 端口不通，HTTPS 推送会卡死或失败。
remote URL 已经是 git@github.com:... 的 SSH 形式，不要改回 https://。
如果推送报 Permission denied (publickey)，说明 SSH 公钥没配好，不要改成 HTTPS 绕开。

【绝对不能提交机密】
.env 里是高德地图 Key、QQ 邮箱 SMTP 授权码、管理员邮箱，已被 .gitignore 排除。
同样被排除的还有 deploy/app.env、*.pem/*.key、__pycache__、客户数据目录、3D 归档。
提交前如果不确定，先跑：git check-ignore -v 文件名
万一误提交了 .env，第一件事是撤销 SMTP 授权码并重置高德 Key。

【车辆资料只改一个文件】
dist/vehicle-facts.js 是全站车辆真实资料的唯一数据源：
年款、具体版本、核定座位、行李件数、驱动、能源、变速箱、Apple CarPlay、日租价、押金，
以及 RENTAL_TERMS 合同条款，都只在这个文件里改。改一处，列表/筛选/详情页同步生效。
没有核实的字段保持 null（页面显示"待确认"），不要凭空编造数值。
不要重新引入 360° 展示、3D 看车、内饰模块 —— 已于 2026-10-13 全部移除，
旧资源归档在 _archive-3d-20261013/（不进仓库、不部署）。

【改前端静态资源要升缓存戳】
dist/index.html 里形如 ?v=20261013-facts-v49 的版本号（当前 21 处）需要同步递增，
否则用户浏览器会用旧缓存。改完 JS/CSS 记得一起升版本号。

请确认你已理解以上约定，然后告诉我你接下来要做的任务。
```

---

## 二、2026-10-13 本次改动清单

| 项目 | 内容 |
| --- | --- |
| 仓库 | `EasonChenGenius/yichen-drive-site`，私有，默认分支 `main` |
| 提交数 | 7 个，基线提交打标签 `v49` |
| 远端地址 | `git@github.com:EasonChenGenius/yichen-drive-site.git`（SSH） |

### 新增文件（都在项目根目录）

| 文件 | 作用 |
| --- | --- |
| `.gitignore` | 排除 `.env`、`deploy/app.env`、`*.pem/*.key`、`__pycache__`、`yichen-service-data/`、`*.db`、`backups/`、`_archive-3d-20261013/`、`dist/*-selection*.html` 等 |
| `CHANGELOG.md` | 从 v49 起逐版本记录改动与待办 |
| `版本留痕说明.md` | 三种留痕方式、查看/对比/回滚命令、取回旧版本、安全排除清单、SSH 排障 |
| `提交本次更新.command` | 双击运行：弹窗填说明 → 提交 → 推送 → 可选打标签 → 打开历史页 |

### 本次之前的改动（已包含在基线 v49）

- 修复「7 座及以上」筛选零结果：`carSeats()` / `carBags()` 在资料未填时按车型类别兜底
- 匹配推荐改为按座位数判断，无结果时放宽偏好并提供「调预算」入口
- 首页「精选车型」精简为 6 辆，每种车型类别各一辆
- 出行人数改为 1–30 连续下拉，行李件数 1–8 件
- 移除 360° 展示、3D 看车、内饰模块（代码 + 资源 + 翻译），three.js 归档至 `_archive-3d-20261013/`
- 新增 `dist/vehicle-facts.js` 作为车辆资料与合同条款的唯一数据源
- `README.md` 中过时的 3D 章节已更正

### 本机环境配置（已生效，不要重复配置）

- SSH 密钥：`~/.ssh/id_ed25519_yichen`
- `~/.ssh/config` 已指定 `github.com` 使用该密钥
- `gh` CLI 已登录 `EasonChenGenius`，但 token 缺 `admin:public_key` scope，无法用 `gh ssh-key add`

---

## 三、云服务（2026-10-15 已开通）

WorkBuddy Cloud Service 已为应用 `wbapp_zfQOMDHL31IfhqEiCsWPcI` 开通，状态正常（计费 normal、资源 assigned）。
它只做一件事：**把客户提交的租车咨询持久保存下来**。托管环境的项目目录只读、数据落 `/tmp`，容器重启即丢，云库就是为了解决这个。

### 数据表

`inquiries`（RLS 已开启）：`request_id / service / car / city / people / bags / duration_days /
start_at / end_at / nickname / phone / wechat / payload(JSONB) / created_at`

### 安全设计 —— 不要改

- **只授予了 `INSERT`**（给 `anon` 与 `authenticated`），**没有任何 SELECT/UPDATE/DELETE 策略**
- 浏览器端只能写、读不回来（实测读回为空数组）
- 目的：客户的手机号、微信号不会从前端泄露
- **不要为了让前端能读而加 SELECT 策略**，也不要给客户发任何可以查到他人记录的链接
- 经营者查看数据只能通过管理端工具，不通过前端页面

### 代码位置

- `dist/cloud-sync.js`：SDK 初始化 + `cloudSaveInquiry()`
  - 用 CDN 形式加载 `@tencent-ai/workbuddy-cloud-sdk@dev`（项目无构建步骤，不要用 npm 形式）
  - `endpoint` / `publishableKey` / `oauthRelayBaseUrl` 三个值必须来自 `publicConfig`，禁止硬编码其他地址
  - `cloudSaveInquiry()` 永不抛错，失败只记录状态 —— **不要让它阻塞或打断原有提交流程**
- `dist/vehicle-business.js` 的 `submitEnquiry()`：后端写库成功后追加一次云端写入
- `dist/index.html`：引入 SDK 与 `cloud-sync.js`

### 部署时必做

v56 起应用脚本合并为 `dist/application-v56.js`（清单见 `scripts/first-paint-sources.json`），
改完源文件必须**先构建、再同步**：

```bash
python3 scripts/build-first-paint.py          # 重新生成 application-v56.js
python3 scripts/build-first-paint.py --check  # 校验产物未落后
rsync -a --delete dist/ webroot/              # 发布用的是 webroot/ 副本，不是 dist/
```

⚠️ **跳过构建会让改动静默失效** —— 产物里没有新代码，页面也不报错，很难发现。

另外：SDK 由 `cloud-sync.js` 内部**按需动态加载**（`ensureCloudSdk()`），
不依赖 index.html 里的 script 标签。**不要把 SDK 的 `<script>` 加回 index.html**，
那会拖慢首屏。

---

## 四、给 Codex 的硬性约定（速查）

1. **改完就提交**，写清楚"改了什么、为什么改"
2. **推送走 SSH**，HTTPS 443 在本机不通
3. **不提交 `.env`** 等机密，提交前用 `git check-ignore -v` 确认
4. **车辆资料只改 `dist/vehicle-facts.js`**，没核实的留 `null`
5. **不要恢复 3D / 360° / 内饰**
6. **改前端静态资源同步升 `dist/index.html` 缓存戳**
7. **回滚用 `git revert`**，不要用 `git reset`（会抹掉历史）

---

## 五、当前待办（按优先级）

1. **填写 12 辆车的真实资料** —— 年款、具体版本、核定座位、行李件数、驱动、能源、变速箱、CarPlay、日租价、押金。清单见 `business/车辆资料核对表-待填写.md`，建议从考斯特、GL8 开始
2. **填写 `RENTAL_TERMS` 的 15 项合同规则** —— 最短租期、免费里程、超公里单价、取消时限、油电政策、事故自负额等，都在 `dist/vehicle-facts.js`
3. **首页搜索框下的照片内容** —— 用户想放一张图，素材尚未提供
4. **上线**：域名、云服务器、ICP 备案、HTTPS 公网部署（详见 `business/上线计划-20261013.md`，配置模板见 `deploy/`）
5. 手机号/邮箱验证与找回密码

---

## 六、常用命令速查

```bash
cd /Users/eason/Documents/Codex/2026-10-04/xia/outputs/yichen-drive-site

git status --short              # 看改了哪些文件
git log --oneline -5            # 看最近 5 个版本
git show <版本号>               # 看某次具体改了什么
git diff                        # 看还没提交的改动
git check-ignore -v <文件名>    # 确认文件是否会被忽略（有输出=安全）

git push origin main            # 推送（SSH，正常几秒内完成）
ssh -T git@github.com           # 验证 SSH 是否配好
```

⚠️ **GitHub 不等于上线。** 仓库只做版本留痕与备份，客户看不到、也跑不了 Flask 后端。真正上线仍需域名 + 云服务器 + ICP 备案。

## 七、v56 发布副本约定（2026-10-16）

首屏HTML与公共样式提前显示，应用脚本由 `scripts/first-paint-sources.json` 指定顺序并生成 `dist/application-v56.js`。修改源文件后必须运行 `python3 scripts/build-first-paint.py`；`python3 scripts/build-first-paint.py --check` 用于校验生成文件未落后。首屏模板与运行时同一段文案需同步修改。原始照片与Logo保留；WebP为发布副本。

本轮仅本地提交，不推送、不打标签；以当前用户授权为准。

## v57 邮箱验证与密码找回（2026-10-17）

- `account_email.py`为服务端验证码：用途／邮箱／账号绑定，HMAC摘要、异步SMTP及SQLite限流；不得改为前端生成或直接信任verified字段。
- `dist/account-security.js`为账户UI。修改后运行生成脚本并校验；发布包名仍为application-v56.js，缓存20261017-auth-v57。
- 旧用户不自动验证；新邮箱注册必须验证码，新手机号注册待短信开通，旧手机号可登录。
- 账号库和邮箱验证记录必须持久化，云端inquiries备份不能替代它们；不要将假邮件测试服务部署到公网。
- 本轮仅本地提交，SMTP真实配置、云端账号保存与真实送达需先确认再发布；未授权自动推送或部署。
