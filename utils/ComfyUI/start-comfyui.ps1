param()
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\Mr\.codex\tmp\ComfyUI'
$py = 'C:\Users\Mr\.codex\tmp\venv-comfyui\Scripts\python.exe'
$out = Join-Path $root 'comfyui.out.log'
$err = Join-Path $root 'comfyui.err.log'

Get-CimInstance Win32_Process |
  Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*ComfyUI*main.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Start-Process -FilePath $py -ArgumentList 'main.py --listen 127.0.0.1 --port 8188' -WorkingDirectory $root -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
Start-Sleep -Seconds 8
try {
  $code = (Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 8).StatusCode
  Write-Output "ComfyUI started, /system_stats status=$code"
} catch {
  Write-Output "ComfyUI start issued, health check pending: $($_.Exception.Message)"
}
