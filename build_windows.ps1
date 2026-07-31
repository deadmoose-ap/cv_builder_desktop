$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
& $PythonBin -c "import sys; assert sys.version_info >= (3, 10), 'CV Builder requires Python 3.10 or newer'"
if ($LASTEXITCODE -ne 0) {
    throw "A compatible Python interpreter was not found."
}

& $PythonBin "tools\build_windows_icon.py"
if ($LASTEXITCODE -ne 0) {
    throw "Could not build the Windows application icon."
}

Remove-Item -Recurse -Force build, dist, installer -ErrorAction SilentlyContinue
& $PythonBin -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name CVBuilder `
    --icon "assets\CVBuilder.ico" `
    --version-file "packaging\windows-version-info.txt" `
    --collect-all reportlab `
    --collect-all customtkinter `
    app.py
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed to build CVBuilder.exe."
}

$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php"
}

$signingEnabled = $env:WINDOWS_PFX_BASE64 -and $env:WINDOWS_PFX_PASSWORD
$certificate = $null
$signTool = $null

try {
    if ($signingEnabled) {
        $certificate = Join-Path $env:TEMP "cvbuilder-signing.pfx"
        [IO.File]::WriteAllBytes(
            $certificate,
            [Convert]::FromBase64String($env:WINDOWS_PFX_BASE64)
        )
        $signTool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Filter signtool.exe -Recurse |
            Where-Object { $_.FullName -match "\\x64\\" } |
            Select-Object -Last 1
        if (-not $signTool) {
            throw "signtool.exe was not found. Install the Windows SDK."
        }
        & $signTool.FullName sign /f $certificate /p $env:WINDOWS_PFX_PASSWORD /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 "dist\CVBuilder\CVBuilder.exe"
        if ($LASTEXITCODE -ne 0) {
            throw "Could not sign CVBuilder.exe."
        }
    }

    & $iscc "packaging\windows-installer.iss"
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed to build the installer."
    }
    $installer = "$PSScriptRoot\installer\CVBuilder-Windows-Setup.exe"

    if ($signingEnabled) {
        & $signTool.FullName sign /f $certificate /p $env:WINDOWS_PFX_PASSWORD /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $installer
        if ($LASTEXITCODE -ne 0) {
            throw "Could not sign the Windows installer."
        }
    }
} finally {
    if ($certificate -and (Test-Path $certificate)) {
        Remove-Item $certificate -Force
    }
}

if (-not (Test-Path $installer)) {
    throw "The Windows installer was not created."
}

Write-Host "Created: $installer"
