---
name: nsis-pack
description: Windows NSIS 安装包打包发布仪式(Electron + electron-builder,可选 PyInstaller 后端)。当用户要"打包/出包/发版/出安装包/打 NSIS/打 exe",或遇到安装包找不到、版本号不一致、exe 属性版本不对、PyInstaller 报 Failed to canonicalize、打包后 import 崩(WinError 127)等问题时使用。覆盖 测试闸→版本同步→tag→干净构建→冒烟→记录→回滚 全流程。
---

# nsis-pack — Electron NSIS 打包发布仪式

把源码变成可分发的 Windows 安装包,并把证据记录进仓库——下次不再"忘记最后打的哪个版本"。

## 流程总览(顺序执行,门禁不过不进下一步)

测试闸 → 版本号同步 → 提交+打 tag → 干净构建 → 冒烟闸 → 回填记录

## 1. 测试闸
- 一条命令全绿才算过(例:`npm run test` = `uv run --extra dev pytest tests/ -x -q`)
- 测试在 uv extra 里时必须带 `--extra dev`,否则报 "program not found"(pytest 根本不在环境,属脚本 bug,修脚本)
- 失败先分诊:产品错 / 测试写宽 / 环境漂移(见踩坑库 5)。不许为过测试放宽断言

## 2. 版本号同步(发版前一次改全)
Electron 项目版本常散落多处,逐处核对:
- `package.json` 的 version(安装包产物名用它)
- Python 后端:`pyproject.toml` + 包内 `__init__.py`
- 其他:安装脚本/资源清单里写死的版本
漏一处 → 产物名与程序内显示版本不一致。

## 3. 提交 + 打 tag
- `git status` 核对只含本轮相关文件;本地数据/缓存/临时产物不提交
- tag `vX.Y.Z` 打在**实际构建的那个提交**上
- 人说了"发布"才打 tag/分发;推远端单独确认

## 4. 干净构建
- 一条链跑完(例:`npm run dist` = electron-vite build + PyInstaller 后端 + electron-builder)
- 构建前工作区必须干净(等价于从 tag 构建),防止本地临时文件进包
- PyInstaller 大依赖(torch 级)单次 5–10 分钟属正常,后台跑
- 构建后抽查产物内无密钥 / .env / 本地数据

## 5. 冒烟闸(单测全绿 ≠ 可用)
启动 `<产物目录>/win-unpacked/<App>.exe` 真实走一遍:
- 进程存活:`tasklist | grep <App>`
- 后端端口起来、首屏 API 返回 200、WebSocket/IPC 连通
- 版本核对以 asar 为准:
  `grep -ao '"version": *"[^"]*"' win-unpacked/resources/app.asar | head -1`
  ⚠️ exe 文件属性里的版本常是 Electron 版本(`signAndEditExecutable:false` 时不写应用版本),别用它判断
- 结束 `taskkill /IM <App>.exe /F` 清理,不留后台进程
- UI 效果由人验收,AI 不能自认通过

## 6. 回填记录
- electron-builder 生成的 `latest.yml` 自带版本号/sha512/size/发布时间 → 摘抄进项目 `docs/RELEASE.md` 发布记录表
- 表列建议:版本 / 日期 / 校验和 / 结果 / 备注(备注写测试与冒烟证据,含 tag→commit)

## 踩坑库(真金白银换来的)

1. **安装包找不到**:electron-builder `directories.output` 可指向仓库外(如 `D:/ydclip-dist`);仓库内 `dist/` 只有渲染产物,别在那找
2. **PyInstaller 直跑报 "Failed to canonicalize script path"**(Windows):用 `python -m PyInstaller`,别用 `pyinstaller` 入口
3. **exe 属性版本 = Electron 版本**:见冒烟闸;以 app.asar 内 package.json 为准
4. **图标只配 `win.icon` 不够**:`nsis.installerIcon` / `uninstallerIcon` 也要配;帮助窗口等子窗口还要把 ico 加进 `extraResources`
5. **venv 依赖漂移**:锁文件正常但 venv 被手动装过包(实例:torch 2.7.0 配 torchaudio 2.11.0 → 原生扩展 `WinError 127`,import 即崩)。pyproject 钉死配套版本(`torchaudio==2.7.0`)+ `uv sync` 校准,再重跑测试闸
6. **重模型依赖**(funasr 类):模型目录缺关键文件时报无意义错误(`'NoneType' object is not callable`)。加载前显式校验文件清单(缺什么报什么),失败删残缺目录重新下载,并允许同进程重试
7. **ProgramFiles 权限**:装到系统目录后相对路径 cache 写不进;显式 `os.makedirs` 到可写目录并设环境变量(如 `MODELSCOPE_CACHE`)

## 回滚
- 旧安装包在产物目录**原地保留**,不覆盖不删(这是回滚材料)
- 安装包形态回滚 = 卸载新版重装旧包;用户数据通常不在安装目录,不受影响
- 没演练过的回滚是假设;首次真实回滚后把实际步骤回填进 `docs/RELEASE.md`
