@echo off
echo Starting DecentSampler Preset Generator...
cd /d "%~dp0"
ds_creator_env\Scripts\python.exe decent_sampler_gui.py
pause
