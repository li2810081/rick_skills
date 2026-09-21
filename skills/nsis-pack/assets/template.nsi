; NSIS 封包模板 (nsis-pack) — 输入: 待分发目录(解压即用); 输出: Setup.exe
; 用法: 装 NSIS (winget install NSIS.NSIS) -> 复制本文件改占位符 -> makensis template.nsi
; 占位符: APPNAME / VERSION / VERSION4 / COMPANY / EXE / SRCDIR
; 能力: 安装 / 记住目录 / 快捷方式 / 升级先卸旧版 / 卸载器+"应用和功能"可见 / 版本元数据 / 免管理员

Unicode true
ManifestDPIAware true
RequestExecutionLevel user

!define APPNAME "APPNAME"
!define VERSION "1.0.0"          ; 显示用三段号
!define VERSION4 "1.0.0.0"       ; VIProductVersion 必须四段
!define COMPANY "COMPANY"
!define EXE "APPNAME.exe"
!define SRCDIR "dist-app\APPNAME"  ; 待分发目录
!define REGKEY "Software\${COMPANY}\${APPNAME}"
!define UNINST_REG "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

VIProductVersion "${VERSION4}"
VIAddVersionKey /LANG=1033 "ProductName" "${APPNAME}"
VIAddVersionKey /LANG=1033 "FileDescription" "${APPNAME} Setup"
VIAddVersionKey /LANG=1033 "FileVersion" "${VERSION4}"
VIAddVersionKey /LANG=1033 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=1033 "CompanyName" "${COMPANY}"

Name "${APPNAME} ${VERSION}"
OutFile "..\dist-installer\${APPNAME}-Setup-${VERSION}.exe"
InstallDir "$LOCALAPPDATA\${COMPANY}\${APPNAME}"
InstallDirRegKey HKCU "${REGKEY}" "InstallDir"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  ; 升级: 有旧版先静默卸掉 (_?= 让卸载器同步跑完, 见 SKILL.md 坑 9)
  ReadRegStr $R0 HKCU "${REGKEY}" "InstallDir"
  StrCmp $R0 "" fresh
  IfFileExists "$R0\Uninstall.exe" 0 fresh
    ExecWait '"$R0\Uninstall.exe" /S _?=$R0'
    Delete "$R0\Uninstall.exe"
    RMDir "$R0"
  fresh:
  SetOutPath "$INSTDIR"
  File /r "${SRCDIR}\*.*"
  WriteRegStr HKCU "${REGKEY}" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  ; 注册进"应用和功能", 用户能从设置里卸载
  WriteRegStr HKCU "${UNINST_REG}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "${UNINST_REG}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINST_REG}" "Publisher" "${COMPANY}"
  WriteRegStr HKCU "${UNINST_REG}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKCU "${UNINST_REG}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINST_REG}" "NoRepair" 1
  ; 快捷方式
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${EXE}"
  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXE}"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  RMDir "$LOCALAPPDATA\${COMPANY}"  ; 空壳才删得掉
  DeleteRegKey HKCU "${UNINST_REG}"
  DeleteRegKey HKCU "${REGKEY}"
  DeleteRegKey HKCU "Software\${COMPANY}"  ; 空壳才删得掉; 公司下还有别的软件键时自动保留
SectionEnd
