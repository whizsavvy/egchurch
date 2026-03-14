# Parse EvergreenSlideMaker/Hymn/hymn.txt and create data/hymns/*.txt
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
if (-not $root) { $root = (Get-Location).Path }
$src = Join-Path $root "EvergreenSlideMaker\Hymn\hymn.txt"
$outDir = Join-Path $root "data\hymns"

if (-not (Test-Path $src)) { Write-Error "Not found: $src"; exit 1 }
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Sanitize-Filename($t) {
    if (-not $t -or -not ($t = $t.Trim())) { return "untitled" }
    $t = $t -replace '[\\/:*?"<>|]', '_' -replace '[\r\n]+', '_'
    $t = $t.Trim('._ ')
    if (-not $t) { return "untitled" }
    if ($t.Length -gt 120) { $t = $t.Substring(0, 120) }
    return $t
}

$text = [System.IO.File]::ReadAllText($src, [System.Text.Encoding]::UTF8)
$text = $text -replace "`r`n", "`n" -replace "`r", "`n"
$blocks = [regex]::Split($text, "(?m)\n(?=\d+\.\s)")
$count = 0
foreach ($block in $blocks) {
    $block = $block.Trim()
    if (-not $block) { continue }
    $lines = $block -split "`n"
    $first = $lines[0] -replace "^\d+\.\s*", ""
    $title = $first.Trim()
    if (-not $title) { continue }
    $contentLines = @()
    if ($lines.Count -gt 1) {
        $contentLines = $lines[1..($lines.Count-1)]
    }
    $content = ($contentLines -join "`n").Trim()
    $name = (Sanitize-Filename $title) + ".txt"
    $path = Join-Path $outDir $name
    [System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))
    $count++
    Write-Host "  $count. $title"
}
Write-Host "`nTotal $count hymns -> $outDir"
