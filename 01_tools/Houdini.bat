:: ************************************************************************
:: Filename: Houdini.bat
:: Created Date: Saturday, April 19th 2025, 12:53:09 pm
:: Author: Mayank Modi
:: ************************************************************************
 
@echo off

:: Set Path
set "SCRIPT_PATH=C:/Users/mayank/Documents/houdini20.5/scripts/"
set "PYTHONPATH=%SCRIPT_PATH%;%PYTHONPATH%"

:: Disable the console window
set "HOUDINI_DISABLE_CONSOLE = 1"

:: Set External Help Browser
set "HOUDINI_EXTERNAL_HELP_BROWSER = 1"


::Start Houdini
set "HOUDINI_DIR=C:\Program Files\Side Effects Software\Houdini 20.5.550\bin" 
set "PATH=%HOUDINI_DIR%;%PATH%"
start houdinifx

exit