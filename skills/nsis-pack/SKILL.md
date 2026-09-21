---
name: nsis-pack
description: NSIS 封包能力:把任意 Windows 应用构建产物(来源不限——PyInstaller/Electron/单 exe/手工目录)封装成专业安装包,含安装/升级覆盖/卸载/快捷方式/静默安装/版本元数据,附发布仪式(测试闸→版本同步→tag→构建→冒烟→记录→回滚)。当用户说"封包/打包/出安装包/做 setup.exe/打 NSIS",或问 NSIS 脚本怎么写、静默安装 /S、升级怎么覆盖旧版、卸载有残留、"应用和功能"里不显示、makensis 报错时使用。
---

# nsis-pack — NSIS 封包能力 + 发布仪式

## 边界
- **核心:封包** — 输入任意"待分发目录",输出专业 Setup.exe。与技术栈无关
- 上游(待分发目录怎么来):见二,速查表;下游发布仪式:见三
- 不做:代码签名、自动更新服务端、商店分发、UI 验收(归人)

## 一、封包核心(主体能力)

### 输入约定
待分发目录 = 解压即用、双击主 exe 就能跑的文件夹(主 exe + 依赖 + 资源)。任何技术栈产出它即可封。

### 模板:`assets/template.nsi`(UTF-8 带 BOM)
复制改 6 个占位符即用:**APPNAME / VERSION / VERSION4 / COMPANY / EXE / SRCDIR**。
已覆盖能力(**全部真机验证过**:编译→静默装→升级→静默卸→零残留):

| 能力 | 实现 |
|---|---|
| 装文件 | SetOutPath + File /r |
| 记住安装目录 | InstallDirRegKey + HKCU 注册表 |
| 开始菜单/桌面快捷方式 | CreateShortCut |
| 升级覆盖旧版 | 读旧目录 → ExecWait 静默卸旧 → 再装 |
| 卸载器 + "应用和功能"可见 | WriteUninstaller + Uninstall 注册表键 |
| 版本可自证 | VIProductVersion(Setup.exe 属性可见,必须四段号) |
| 免管理员 | RequestExecutionLevel user,装 $LOCALAPPDATA |

### 编译与自检(封包能力自己也要冒烟)
1. 先建 OutFile 所在目录(NSIS 不自动建)→ `makensis template.nsi` 出包
2. `Setup.exe /S` 静默装 → 校验:文件齐、快捷方式在、"应用和功能"有条目
3. **再装一遍** — 验升级路径(静默卸旧再装)不炸
4. `Uninstall.exe /S` → 校验零残留:安装目录、快捷方式、注册表键全清
5. 带界面装一次,点一遍主流程(用户看的是这个)

## 二、上游速查:待分发目录从哪来

| 来源 | 命令 | 产物 |
|---|---|---|
| Python | `python -m PyInstaller app.spec --noconfirm --distpath dist-app`(onedir;勿直跑 pyinstaller 入口,坑 2) | dist-app/\<name\>/ |
| Electron | `electron-builder --dir` | win-unpacked/ |
| 单 exe / 绿色软件 | 拷到约定目录 | 目录本身 |

- Electron 壳 + Python 后端:后端 onedir 经 extraResources 嵌进壳,封包对象 = 壳的 win-unpacked
- 上游构建大依赖(torch 级)单次 5–10 分钟属正常,后台跑;构建前工作区干净,产物内无密钥/.env/本地数据

## 三、发布仪式(封包进项目工程后)

### 1. 测试闸
- 一条命令全绿才算过(例:`uv run --extra dev pytest tests/ -x -q`)
- 测试在 uv extra 里必须带 `--extra dev`,否则报 "program not found"(脚本 bug,修脚本)
- 失败先分诊:产品错 / 测试写宽 / 环境漂移(坑 5)。不许为过测试放宽断言

### 2. 版本号同步(一次改全)
- Electron:`package.json` version;Python:`pyproject.toml` + 包内 `__init__.py`
- 用模板封包时:`template.nsi` 里的 VERSION/VERSION4 也是同步点
- 漏一处 → 产物名与程序内显示版本不一致

### 3. 提交 + 打 tag
- `git status` 核对只含本轮相关文件;本地数据/缓存/临时产物不提交
- tag `vX.Y.Z` 打在**实际构建的那个提交**上;人说"发布"才打 tag/分发,推远端单独确认

### 4. 构建
- 一条链跑完;构建前工作区必须干净(等价于从 tag 构建)
- 构建后抽查产物内无密钥 / .env / 本地数据

### 5. 冒烟闸(单测全绿 ≠ 可用)
- 先做一.编译与自检的四步;再**真实启动应用**走主流程
- Electron 版本核对:`grep -ao '"version": *"[^"]*"' win-unpacked/resources/app.asar | head -1`;⚠️ exe 属性版本可能是 Electron 版本(`signAndEditExecutable:false`),别用它判断
- 结束 `taskkill /IM <App>.exe /F` 清理;UI 效果由人验收,AI 不能自认通过

### 6. 回填记录
- electron-builder:`latest.yml` 自带版本/sha512/size/时间 → 摘抄进项目 `docs/RELEASE.md`
- makensis:手动 `certutil -hashfile <Setup.exe> SHA512`
- 表列建议:版本 / 日期 / 校验和 / 结果 / 备注(测试与冒烟证据,含 tag→commit)

## 踩坑库(真金白银换来的)

1. **安装包找不到**:electron-builder `directories.output` 可指向仓库外;仓库内 `dist/` 可能只有渲染产物,别在那找
2. **PyInstaller 直跑报 "Failed to canonicalize script path"**(Windows):用 `python -m PyInstaller`,别用 `pyinstaller` 入口
3. **exe 属性版本 ≠ 应用版本**:Electron 场景见仪式 5;自封包场景用 VIProductVersion 让属性真实可证
4. **图标只配 `win.icon` 不够**:`nsis.installerIcon` / `uninstallerIcon` 也要配;子窗口还要 ico 进 `extraResources`
5. **venv 依赖漂移**:锁文件正常但 venv 被手动装过包(实例:torch 2.7.0 配 torchaudio 2.11.0 → `WinError 127`,import 即崩)。钉死配套版本 + `uv sync` 校准,重跑测试闸
6. **重模型依赖**(funasr 类):缺关键文件报无意义错误(`'NoneType' object is not callable`)。加载前校验文件清单,失败删残缺目录重下,允许同进程重试
7. **ProgramFiles 权限**:装系统目录后相对路径 cache 写不进;显式 `os.makedirs` 到可写目录并设环境变量(如 `MODELSCOPE_CACHE`)
8. **png 改后缀当 ico**:构建期或图标直接炸;用真多尺寸 ico 转换工具
9. **ExecWait 卸旧版必须加 `_?=<旧目录>`**:不加时卸载器把自己复制到临时目录后立即返回,旧文件没删完新文件就开写,升级后文件错乱
10. **Git Bash 调安装器 `/S` 被转义成路径**(安装器收不到静默指令,弹 GUI 窗):前缀 `MSYS2_ARG_CONV_EXCL='*'`
11. **makensis 报 "Bad text encoding"**:.nsi 含中文时必须存 **UTF-8 带 BOM**(无 BOM 会按 ACP 解析直接失败)
12. **"Can't open output file"**:OutFile 目录不存在;NSIS 不自动建目录
13. **卸载残留父级壳**:`DeleteRegKey`/`RMDir` 只删最末级,注册表公司键和 LocalAppData 公司目录会剩空壳;卸载节补删父级(非空时 NSIS 自动保留,安全)

## 回滚
- 旧安装包在产物目录**原地保留**,不覆盖不删(这是回滚材料)
- 安装包形态回滚 = 卸载新版重装旧包;用户数据通常不在安装目录,不受影响
- 没演练过的回滚是假设;首次真实回滚后把实际步骤回填进 `docs/RELEASE.md`
