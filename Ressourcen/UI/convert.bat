@ECHO OFF

cd /d %0\..

for /r %%f in (*.ui) do (
    ECHO ..\..\..\Sephrasto\venv\Scripts\pyside6-uic.exe %%~nf.ui -o ../%%~nf.py
    CALL ..\..\..\Sephrasto\venv\Scripts\pyside6-uic.exe %%~nf.ui -o ../%%~nf.py
)

PAUSE