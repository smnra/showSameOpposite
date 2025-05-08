@ECHO OFF

set OSGEO4W_ROOT=C:\Program Files\QGIS 3.42.1

set PATH=%OSGEO4W_ROOT%\bin;%PATH%
set PATH=%PATH%;%OSGEO4W_ROOT%\apps\qgis\bin

@echo off
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
@echo off
path %OSGEO4W_ROOT%\apps\qgis\bin;%OSGEO4W_ROOT%\apps\grass\grass\lib;%OSGEO4W_ROOT%\apps\grass\grass\bin;%PATH%

cd /d %~dp0


::Resources
call pyrcc5 resources.qrc -o resources.py

@ECHO OFF
GOTO END

:ERROR
   echo "Failed!"
   set ERRORLEVEL=%ERRORLEVEL%
   pause

:END
@ECHO ON

Pause