$ErrorActionPreference = "Stop"

if (!(Test-Path ".venv")) {
    powershell -ExecutionPolicy Bypass -File ".\scripts\setup.ps1"
}

$pipIndexArgs = @(
    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
    "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
)

& ".\.venv\Scripts\python.exe" -m pip install @pipIndexArgs pyinstaller
& ".\.venv\Scripts\python.exe" -m PyInstaller `
    --onefile `
    --name "ExamTrainerLauncher" `
    --distpath "." `
    --workpath ".\launcher\build" `
    --specpath ".\launcher" `
    ".\launcher\trainer_launcher.py"

Write-Host "Built .\ExamTrainerLauncher.exe"

