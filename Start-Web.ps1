param([int]$Port = 8765, [switch]$LAN)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$bindAddress = if ($LAN) { '0.0.0.0' } else { '127.0.0.1' }
Write-Host "study-canvas: http://localhost:$Port"
if ($LAN) { Write-Host '同じWi-Fiのスマホでは http://このPCのIPv4アドレス:ポート を開いてください。' }
Write-Host '終了するには Ctrl+C。記録はブラウザごとに保存されます。'
Start-Process "http://localhost:$Port"
python -m http.server $Port --bind $bindAddress --directory web
