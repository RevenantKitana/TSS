# PowerShell Script: Auto-refresh VM resources every 5s
$SSHKey = Join-Path $PSScriptRoot "168.107.86.20.key"
$VMHost = "168.107.86.20"
$VMUser = "ubuntu"

$remoteCmd = "echo '=== 1. CPU & UPTIME ==='; lscpu | grep 'Model name'; uptime; echo ''; echo '=== 2. RAM & SWAP ==='; free -h; echo ''; echo '=== 3. DISK STORAGE ==='; df -h /; echo ''; echo '=== 4. ZEROTTS SERVICE ==='; systemctl status zerotts --no-pager | head -n 7"

while ($true) {
    Clear-Host
    ssh -i "$SSHKey" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$VMUser@$VMHost" $remoteCmd

    Write-Host ""
    Write-Host "===============================================================================" -ForegroundColor Cyan
    Write-Host " [Nhan Ctrl+C de dung] - Tu dong lam moi sau 5s..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 5
}
