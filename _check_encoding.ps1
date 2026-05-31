$path = "f:\0_MyNote\0_博士\4_Games\0_Main\0_ManagementSystem\启动系统.bat"
$bytes = [System.IO.File]::ReadAllBytes($path)
Write-Host ("File size: " + $bytes.Length + " bytes")
Write-Host ("First 30 bytes: " + ($bytes[0..29] -join " "))
$crlf=0; $lf=0; $cr=0
for($i=0; $i -lt $bytes.Length-1; $i++) {
    if ($bytes[$i] -eq 13 -and $bytes[$i+1] -eq 10) { $crlf++ }
    elseif ($bytes[$i] -eq 10) { $lf++ }
    elseif ($bytes[$i] -eq 13) { $cr++ }
}
Write-Host ("CRLF: $crlf, Lone LF: $lf, Lone CR: $cr")