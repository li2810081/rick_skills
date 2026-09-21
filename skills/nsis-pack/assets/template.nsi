; Python 应用 NSIS 安装包最小模板 (nsis-pack 路线 B)
; 用法: 装 NSIS (winget install NSIS.NSIS) → 复制本文件改占位符 → makensis template.nsi
; 占位符全大写: APPNAME / VERSION / COMPANY / EXE / SRCDIR

Unicode true
ManifestDPIAware true
RequestExecutionLevel user

!define APPNAME "APPNAME"
!define VERSION "1.0.0"
!define COMPANY "COMPANY"
!define EXE "APPNAME.exe"
!define SRCDIR "dist-app\APPNAME"   ; PyInstaller onedir 输出目录

Name "${APPNAME} ${VERSION}"
OutFile "..\dist-installer\${APPNAME}-Setup-${VERSION}.exe"
InstallDir "$LOCALAPPDATA\${COMPANY}\${APPNAME}"
InstallDirRegKey HKCU "Software\${COMPANY}\${APPNAME}" "InstallDir"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "${SRCDIR}\*.*"
  WriteRegStr HKCU "Software\${COMPANY}\${APPNAME}" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${EXE}"
  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXE}"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  DeleteRegKey HKCU "Software\${COMPANY}\${APPNAME}"
SectionEnd
