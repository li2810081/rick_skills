---
name: nsis-pack
description: 把开发完的 Python 或 Electron 应用打包成 NSIS 安装包并走完发布仪式。当用户说"打包/出包/发版/出安装包/打 NSIS/封个安装包"(尤其项目还没配过打包、从零开始),或遇到安装包找不到、版本号不一致、exe 属性版本不对、PyInstaller 报 Failed to canonicalize、打包后 import 崩(WinError 127)时使用。覆盖 首次接入(Electron/纯 Python/混合三路线)→测试闸→版本同步→tag→构建→冒烟→记录→回滚;不做代码签名、自动更新服务、商店分发。
---

# nsis-pack — Python/Electron 应用 NSIS 打包发布仪式

## 边界:从哪步做到哪步
- **起点**:应用开发完成,开发机上能跑通主流程(打包不是修 bug 的手段)
- **终点**:安装包生成 + 冒烟通过 + 发布记录回填 `docs/RELEASE.md` + 回滚材料就位
- **不做**:代码签名(证书/时间戳)、electron-updater 自动更新服务端、应用商店分发、UI 效果验收(归人)

## 第 0 步 · 首次接入(项目还没配过打包基建时,按形态三选一)

| 项目形态 | 路线 |
|---|---|
| Electron | A:electron-builder 直出 NSIS |
| 纯 Python(GUI/服务) | B:PyInstaller onedir → makensis 封装 |
| Electron 壳 + Python 后端 | C:B 出后端,A 加 extraResources 内嵌 |

### 路线 A · Electron
1. `npm i -D electron-builder`
2. package.json 加最小 build 配置:
```json
{
  "build": {
    "appId": "com.<yourname>.<appname>",
    "productName": "AppName",
    "directories": { "output": "D:/dist-appname" },
    "files": ["out/**/*"],
    "win": { "target": "nsis", "icon": "build/icon.ico" },
    "nsis": {
      "oneClick": false,
      "perMachine": false,
      "allowToChangeInstallationDirectory": true,
      "installerIcon": "build/icon.ico",
      "uninstallerIcon": "build/icon.ico"
    }
  }
}
```
   `output` 故意指到仓库外(防误提交,见坑 1);`icon` 必须是真 .ico 多尺寸文件,**png 改后缀会炸**(见坑 8)
3. 校验:`main` 字段指向的文件真实存在;`scripts.dist` = 前端构建命令 + `electron-builder`

### 路线 B · 纯 Python
1. 写 PyInstaller spec:**onedir 不用 onefile**(启动快、少杀软误报);`datas` 带上静态资源,`hiddenimports` 补动态导入
2. 构建:`python -m PyInstaller app.spec --noconfirm --distpath dist-app`(Windows 勿直跑 `pyinstaller` 入口,见坑 2)
3. NSIS 封装:`winget install NSIS.NSIS` → 复制 `assets/template.nsi` 改占位符(APPNAME/VERSION/COMPANY/EXE/SRCDIR)→ `makensis template.nsi` 出 Setup.exe
4. 静默装/卸(冒烟用):`Setup.exe /S` / `Uninstall.exe /S`

### 路线 C · Electron 壳 + Python 后端
1. 后端按路线 B 第 1–2 步出 onedir
2. Electron 侧按路线 A 配好,build 里追加:
```json
"extraResources": [{ "from": "dist-app/<backend-name>", "to": "<backend-name>" }]
```
3. 主进程用 `process.resourcesPath/<backend-name>/` 拼 exe 路径 spawn;前端在后端就绪前不发业务请求

## 配好基建后,三条路线进同一套仪式

### 1. 测试闸
- 一条命令全绿才算过(例:`uv run --extra dev pytest tests/ -x -q`)
- 测试在 uv extra 里时必须带 `--extra dev`,否则报 "program not found"(属脚本 bug,修脚本)
- 失败先分诊:产品错 / 测试写宽 / 环境漂移(见坑 5)。不许为过测试放宽断言

### 2. 版本号同步(一次改全)
逐处核对,漏一处 → 产物名与程序内显示版本不一致:
- Electron:`package.json` version(产物名来源)
- Python:`pyproject.toml` + 包内 `__init__.py`
- 其他写死版本的地方(安装脚本/资源清单/关于页)

### 3. 提交 + 打 tag
- `git status` 核对只含本轮相关文件;本地数据/缓存/临时产物不提交
- tag `vX.Y.Z` 打在**实际构建的那个提交**上
- 人说了"发布"才打 tag/分发;推远端单独确认

### 4. 构建
- 一条链跑完;构建前工作区必须干净(等价于从 tag 构建)
- PyInstaller 大依赖(torch 级)单次 5–10 分钟属正常,后台跑
- 构建后抽查产物内无密钥 / .env / 本地数据

### 5. 冒烟闸(单测全绿 ≠ 可用)
- Electron:启动 `<产物目录>/win-unpacked/<App>.exe` → 进程存活(`tasklist | grep <App>`)→ 后端端口/首屏 API 200/WS 连通
- 纯 Python:先直接跑 `dist-app/<App>.exe` 走主流程;再 `Setup.exe /S` 静默安装一遍从安装目录启动验证
- 版本核对以应用内真实配置为准:
  Electron 用 `grep -ao '"version": *"[^"]*"' win-unpacked/resources/app.asar | head -1`;
  ⚠️ exe 文件属性里的版本常是 Electron 版本(`signAndEditExecutable:false` 时不写应用版本),别用它判断
- 结束 `taskkill /IM <App>.exe /F` 清理,不留后台进程
- UI 效果由人验收,AI 不能自认通过

### 6. 回填记录
- electron-builder 的 `latest.yml` 自带版本/sha512/size/发布时间 → 摘抄进项目 `docs/RELEASE.md`
- makensis 路线手动算:`certutil -hashfile <Setup.exe> SHA512`
- 表列建议:版本 / 日期 / 校验和 / 结果 / 备注(测试与冒烟证据,含 tag→commit)

## 踩坑库(真金白银换来的)

1. **安装包找不到**:electron-builder `directories.output` 可指向仓库外;仓库内 `dist/` 可能只有渲染产物,别在那找
2. **PyInstaller 直跑报 "Failed to canonicalize script path"**(Windows):用 `python -m PyInstaller`,别用 `pyinstaller` 入口
3. **exe 属性版本 = Electron 版本**:见冒烟闸;以 app.asar 内配置为准
4. **图标只配 `win.icon` 不够**:`nsis.installerIcon` / `uninstallerIcon` 也要配;子窗口还要把 ico 加进 `extraResources`
5. **venv 依赖漂移**:锁文件正常但 venv 被手动装过包(实例:torch 2.7.0 配 torchaudio 2.11.0 → 原生扩展 `WinError 127`,import 即崩)。钉死配套版本 + `uv sync` 校准,再重跑测试闸
6. **重模型依赖**(funasr 类):模型目录缺关键文件时报无意义错误(`'NoneType' object is not callable`)。加载前显式校验文件清单(缺什么报什么),失败删残缺目录重下,允许同进程重试
7. **ProgramFiles 权限**:装到系统目录后相对路径 cache 写不进;显式 `os.makedirs` 到可写目录并设环境变量(如 `MODELSCOPE_CACHE`)
8. **png 改后缀当 ico**:electron-builder 构建期或安装包图标直接炸;用真多尺寸 ico(png2ico/ffmpeg 转换)

## 回滚
- 旧安装包在产物目录**原地保留**,不覆盖不删(这是回滚材料)
- 安装包形态回滚 = 卸载新版重装旧包;用户数据通常不在安装目录,不受影响
- 没演练过的回滚是假设;首次真实回滚后把实际步骤回填进 `docs/RELEASE.md`
