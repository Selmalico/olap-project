@echo off
REM Complete cleanup - removes all documentation and temporary files
REM Keeps only project folders ready for professor

cd /d c:\Users\selma_3ct5ekw\Desktop\olap\olap-project

echo.
echo ════════════════════════════════════════════════════════════════
echo          Cleaning Project Structure
echo ════════════════════════════════════════════════════════════════
echo.

REM Delete root level documentation files
echo Removing documentation files...
if exist "DELIVERY_SUMMARY.txt" del /Q DELIVERY_SUMMARY.txt
if exist "BEANSTALK_DEPLOYMENT_GUIDE.md" del /Q BEANSTALK_DEPLOYMENT_GUIDE.md
if exist "BEANSTALK_QUICK_REFERENCE.txt" del /Q BEANSTALK_QUICK_REFERENCE.txt
if exist "BEANSTALK_DEPLOYMENT_CHECKLIST.txt" del /Q BEANSTALK_DEPLOYMENT_CHECKLIST.txt
if exist "BEANSTALK_ARCHITECTURE_DIAGRAM.txt" del /Q BEANSTALK_ARCHITECTURE_DIAGRAM.txt
if exist "BEANSTALK_CONFIGURATION_COMPLETE.txt" del /Q BEANSTALK_CONFIGURATION_COMPLETE.txt
if exist "BEANSTALK_GUIDE_INDEX.md" del /Q BEANSTALK_GUIDE_INDEX.md
if exist "BEANSTALK_READY.txt" del /Q BEANSTALK_READY.txt
if exist "INTEGRATION_SUMMARY.md" del /Q INTEGRATION_SUMMARY.md
if exist "AGENTS_INTEGRATION.md" del /Q AGENTS_INTEGRATION.md
if exist "API_REFERENCE_ENRICHED.md" del /Q API_REFERENCE_ENRICHED.md
if exist "VISUAL_GUIDE.md" del /Q VISUAL_GUIDE.md
if exist "CHANGES_SUMMARY.md" del /Q CHANGES_SUMMARY.md
if exist "CLEANUP_GUIDE.md" del /Q CLEANUP_GUIDE.md
if exist "QUICK_SUMMARY.txt" del /Q QUICK_SUMMARY.txt
if exist "COMPLETION_CHECKLIST.txt" del /Q COMPLETION_CHECKLIST.txt
if exist "VERIFY_SETUP.bat" del /Q VERIFY_SETUP.bat
if exist "ER_DIAGRAM_UPDATE_SUMMARY.md" del /Q ER_DIAGRAM_UPDATE_SUMMARY.md
if exist "UPDATE_ER_DIAGRAM_INSTRUCTIONS.md" del /Q UPDATE_ER_DIAGRAM_INSTRUCTIONS.md
if exist "update_er_diagram.py" del /Q update_er_diagram.py
if exist "update_er_diagram.bat" del /Q update_er_diagram.bat
if exist "README_DOCUMENTATION.md" del /Q README_DOCUMENTATION.md
if exist "INTEGRATION_COMPLETE.bat" del /Q INTEGRATION_COMPLETE.bat
if exist "CHANGES_APPLIED.bat" del /Q CHANGES_APPLIED.bat
if exist "BRANDING_REPLACEMENT_COMPLETE.txt" del /Q BRANDING_REPLACEMENT_COMPLETE.txt
if exist "BACKEND_HANGING_FIXED.txt" del /Q BACKEND_HANGING_FIXED.txt
if exist "BACKEND_FIX_SUMMARY.txt" del /Q BACKEND_FIX_SUMMARY.txt
if exist "QUICK_START_BACKEND.txt" del /Q QUICK_START_BACKEND.txt
if exist "FIX_VERIFICATION.txt" del /Q FIX_VERIFICATION.txt
if exist "BEANSTALK_DEPLOYMENT_ERROR_FIXED.txt" del /Q BEANSTALK_DEPLOYMENT_ERROR_FIXED.txt
if exist "DEPLOYMENT_FIX_SUMMARY.txt" del /Q DEPLOYMENT_FIX_SUMMARY.txt
if exist "NEXT_STEPS.txt" del /Q NEXT_STEPS.txt
if exist "START_HERE_BEANSTALK.txt" del /Q START_HERE_BEANSTALK.txt
if exist "AWS_UI_DEPLOYMENT_GUIDE.md" del /Q AWS_UI_DEPLOYMENT_GUIDE.md
if exist "AWS_UI_VISUAL_GUIDE.txt" del /Q AWS_UI_VISUAL_GUIDE.txt
if exist "AWS_UI_QUICK_START.txt" del /Q AWS_UI_QUICK_START.txt
if exist "COMPLETE_AWS_UI_DEPLOYMENT_GUIDE.md" del /Q COMPLETE_AWS_UI_DEPLOYMENT_GUIDE.md
if exist "AWS_UI_DEPLOYMENT_PACKAGE_SUMMARY.txt" del /Q AWS_UI_DEPLOYMENT_PACKAGE_SUMMARY.txt
if exist "AWS_UI_DEPLOYMENT_INDEX.txt" del /Q AWS_UI_DEPLOYMENT_INDEX.txt
if exist "INTEGRATION_COMPLETE.bat" del /Q INTEGRATION_COMPLETE.bat
if exist "CLEAN_PROJECT.bat" del /Q CLEAN_PROJECT.bat

echo Removing backend helper files...
if exist "backend\create_deployment_package.bat" del /Q backend\create_deployment_package.bat
if exist "backend\diagnostics.py" del /Q backend\diagnostics.py
if exist "backend\start_backend.bat" del /Q backend\start_backend.bat
if exist "backend\redeploy.bat" del /Q backend\redeploy.bat

echo Removing root batch files...
if exist "cleanup_unused_files.bat" del /Q cleanup_unused_files.bat
if exist "setup_and_run.bat" del /Q setup_and_run.bat

echo Removing __pycache__ and .pyc files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo ════════════════════════════════════════════════════════════════
echo ✅ Project Cleaned Successfully!
echo ════════════════════════════════════════════════════════════════
echo.
echo Remaining structure:
echo.
echo olap-project/
echo ├── backend/              Main backend code
echo ├── frontend/             React frontend
echo ├── data/                 CSV and DuckDB
echo ├── database/             Schema files
echo ├── docs/                 Architecture docs
echo ├── infrastructure/       Cloud setup files
echo ├── generate_dataset.py
echo ├── README.md             Project overview
echo └── .gitignore
echo.
echo Ready to share with professor!
echo.
pause
