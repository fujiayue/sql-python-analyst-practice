$ErrorActionPreference = "Stop"

function Get-PreferredPython {
    $candidates = @(
        "$env:APPDATA\uv\python\cpython-3.11.15-windows-x86_64-none\python.exe",
        "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
        "python"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -eq "python") {
            $cmd = Get-Command python -ErrorAction SilentlyContinue
            if ($cmd) {
                return $cmd.Source
            }
        }
        elseif (Test-Path $candidate) {
            return $candidate
        }
    }
    throw "No Python executable found."
}

$venvPython = ".\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $version = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($version -eq "3.14") {
        $repoRoot = (Resolve-Path ".").Path
        $venvPath = (Resolve-Path ".\.venv").Path
        if (!$venvPath.StartsWith($repoRoot)) {
            throw "Refusing to remove venv outside repository: $venvPath"
        }
        Remove-Item -LiteralPath $venvPath -Recurse -Force
    }
}

$pipIndexArgs = @(
    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
    "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
)

if (!(Test-Path ".venv")) {
    $python = Get-PreferredPython
    & $python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install @pipIndexArgs --upgrade "pip<26"
& ".\.venv\Scripts\python.exe" -m pip install @pipIndexArgs -r ".\backend\requirements.txt"

Push-Location ".\frontend"
try {
    cmd /c npm install
}
finally {
    Pop-Location
}

Write-Host "Setup complete."
