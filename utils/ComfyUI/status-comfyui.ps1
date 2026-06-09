param()
$ErrorActionPreference = 'Stop'
try {
  $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 8
  "ComfyUI UP status=$($r.StatusCode)"
} catch {
  "ComfyUI DOWN: $($_.Exception.Message)"
}
Get-NetTCPConnection -LocalPort 8188 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,State,OwningProcess
