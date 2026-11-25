@echo off
echo Budowanie Geant4UnityPlugin...

cd build
cmake .. -G "Visual Studio 16 2019" -A x64
cmake --build . --config Release

echo.
echo Skopiuj biblioteke do Unity...
copy Release\GeantUnityPlugin.dll ..\UnityProject\Assets\Plugins\GeantUnityPlugin.dll

echo.
echo Gotowe!
pause
