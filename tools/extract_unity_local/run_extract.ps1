param(
    [string]$VideoPath = "",
    [string]$InputDir = "$PSScriptRoot\input_videos"
)

$env:Path = "$env:Path;C:\Program Files\FormatFactory;$PSScriptRoot\tesseract"
$env:TESSDATA_PREFIX = "$PSScriptRoot\tesseract\tessdata"

if ($VideoPath -and (Test-Path $VideoPath)) {
    if (-not (Test-Path $InputDir)) {
        New-Item -ItemType Directory -Path $InputDir -Force | Out-Null
    }
    $targetVideo = Join-Path $InputDir (Split-Path $VideoPath -Leaf)
    if (-not (Test-Path $targetVideo)) {
        Copy-Item -Path $VideoPath -Destination $targetVideo -Force
    }
}

if (-not (Test-Path $InputDir)) {
    New-Item -ItemType Directory -Path $InputDir -Force | Out-Null
}

$script = "$PSScriptRoot\extract_unity_local.ps1"
& $script -InputFolder $InputDir -IntervalSeconds 3 -SkipInstall

