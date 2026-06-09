param()
$ErrorActionPreference = 'Stop'
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*ComfyUI*main.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "Stopped PID=$($_.ProcessId)" }
