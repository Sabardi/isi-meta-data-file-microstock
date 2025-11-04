@echo off
setlocal ENABLEDELAYEDEXPANSION
title Metadata Applier

echo ===============================
echo  Metadata Applier (Windows)
echo ===============================
echo.
echo Masukkan path folder yang berisi file media dan CSV-nya.
set /p FOLDER=Folder path: 

if "%FOLDER%"=="" (
  echo [ERROR] Folder path kosong.
  pause
  exit /b 1
)

if not exist "%FOLDER%" (
  echo [ERROR] Folder tidak ditemukan: "%FOLDER%"
  pause
  exit /b 1
)

rem Cari Python: coba python, lalu py -3
set "PYTHON="
where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON (
  where py >nul 2>&1 && set "PYTHON=py -3"
)
if not defined PYTHON (
  echo [ERROR] Python tidak ditemukan. Install Python 3.8+ terlebih dahulu.
  echo Unduh: https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

rem Opsional: gunakan exiftool.exe jika ada di folder yang sama
set "EXIF_OPT="
set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%exiftool.exe" (
  set "EXIF_OPT=--exiftool \"%SCRIPT_DIR%exiftool.exe\""
)

echo.
set "DRYFLAG=--dry-run"
set /p DRY=Jalankan sebagai DRY-RUN dulu? [Y/n]: 
if /I "%DRY%"=="n" set "DRYFLAG="

echo.
echo Menjalankan...
echo Folder : "%FOLDER%"
echo Script : "%SCRIPT_DIR%metadata_applier.py"
echo.

%PYTHON% "%SCRIPT_DIR%metadata_applier.py" --dir "%FOLDER%" %DRYFLAG% %EXIF_OPT%
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%" NEQ "0" (
  echo Proses selesai dengan kode exit %EXITCODE%.
  echo Jika error "exiftool not found", instal exiftool atau taruh exiftool.exe di folder yang sama dengan file BAT ini.
)
pause
exit /b %EXITCODE%


