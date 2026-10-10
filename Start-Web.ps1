param([int]$Port = 8765, [switch]$LAN)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$bindAddress = if ($LAN) { '0.0.0.0' } else { '127.0.0.1' }
Write-Host "study-canvas: http://localhost:$Port"
if ($LAN) { Write-Host '同じWi-Fiのスマホでは http://このPCのIPv4アドレス:ポート を開いてください。' }
Write-Host '終了するには Ctrl+C。記録はブラウザごとに保存されます。'
$webRoot = 'web'
if (Test-Path -LiteralPath 'private-data/material/packs.json') {
  node scripts/build-private.mjs
  if ($LASTEXITCODE -ne 0) { throw '個人用教材の準備に失敗しました。教材の生成手順を確認してください。' }
  $webRoot = 'build/private/web'
  $textPointer = 'build/material-transcription/current.json'
  $textCurrent = if (Test-Path -LiteralPath $textPointer) { Get-Content -LiteralPath $textPointer -Raw | ConvertFrom-Json }
  $textManifest = if ($textCurrent) { Get-Content -LiteralPath (Join-Path $textCurrent.directory 'manifest.json') -Raw | ConvertFrom-Json }
  $sourceHash = (Get-FileHash -LiteralPath 'build/private/manifest.json' -Algorithm SHA256).Hash.ToLowerInvariant()
  $compactCurrent = if (Test-Path -LiteralPath 'build/private-compact/current.json') { Get-Content -LiteralPath 'build/private-compact/current.json' -Raw | ConvertFrom-Json }
  $compactHash = if ($compactCurrent) { (Get-FileHash -LiteralPath (Join-Path $compactCurrent.directory 'manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() }
  if (-not $textManifest -or -not $textManifest.transcription.allImagesAttempted -or $textManifest.transcription.cropMethod -ne 4 -or $textManifest.compaction.sourceManifestSha256 -ne $sourceHash -or $textManifest.transcription.sourceManifestSha256 -ne $compactHash) {
    Write-Host '問題・解答・解説を文字化しています。初回のOCRには時間がかかります。'
    npm run build:private-compact
    if ($LASTEXITCODE -ne 0) { throw '教材の文字化に失敗しました。前回の成功ビルドと原本は保持しています。' }
    $textCurrent = Get-Content -LiteralPath $textPointer -Raw | ConvertFrom-Json
  }
  $webRoot = Join-Path $textCurrent.directory 'web'
  Get-ChildItem -LiteralPath 'web' -File | Where-Object Name -NotIn @('catalog.mjs', 'library-catalog.mjs') | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $webRoot $_.Name)
  }
}
Start-Process "http://localhost:$Port"
python -m http.server $Port --bind $bindAddress --directory $webRoot
