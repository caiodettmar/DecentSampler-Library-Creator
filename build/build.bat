@echo off
echo Building DecentSampler Library Creator...
echo.

REM Activate virtual environment
call ds_creator_env\Scripts\activate

REM Install build dependencies
echo Installing build dependencies...
pip install pyinstaller auto-py-to-exe

REM Run the build script
echo Running build script...
python build_standalone.py

echo.
echo Build complete! Check the dist folder for the executable.
echo.
pause