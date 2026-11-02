# =============================================================================
# KICH BAN TIEM LOI & KIEM CHUNG KHA NANG PHUC HOI (CHAOS FAILOVER TEST)
# Muc dich: Chu dong dung 1 ban sao ung dung (app-replica-1) khi dang co tai
# de do thoi gian phat hien loi, chuyen doi du phong (RTO) va ty le loi.
# Cach chay: powershell -ExecutionPolicy Bypass -File .\tests\chaos_failover_test.ps1
# =============================================================================

param(
    [string]$TargetUrl = "http://localhost:8080/health",
    [string]$VictimContainer = "app-replica-1"
)

$env:Path += ";C:\Program Files\Docker\Docker\resources\bin"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " THUC NGHIEM TIEM LOI & DO THOI GIAN PHUC HOI (RTO) - DE TAI 1" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

$LogFile = "tests\data\failover_experiment_log.csv"
New-Item -ItemType Directory -Force -Path "tests\data" | Out-Null
"step,timestamp,http_status,latency_ms,served_by_node,phase" | Out-File -FilePath $LogFile -Encoding utf8

Write-Host "`n[Giai doan 1] Gui 10 request kiem tra trang thai binh thuong (2 Replicas cung chay)..." -ForegroundColor Green
for ($i = 1; $i -le 10; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-RestMethod -Uri "${TargetUrl}?r=$i" -Method Get -TimeoutSec 3
        $sw.Stop()
        $ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        Write-Host ("  #{0:D2} | HTTP 200 | {1,6} ms | Node: {2}" -f $i, $ms, $resp.node_id)
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),200,$ms,$($resp.node_id),Normal_Before_Fault" | Add-Content -Path $LogFile
    } catch {
        $sw.Stop()
        Write-Host ("  #{0:D2} | ERROR    | Request failed" -f $i) -ForegroundColor Red
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),502,$($sw.Elapsed.TotalMilliseconds),ERROR,Normal_Before_Fault" | Add-Content -Path $LogFile
    }
    Start-Sleep -Milliseconds 150
}

Write-Host "`n[Giai doan 2] TIEM LOI: Chu dong dung container '$VictimContainer'..." -ForegroundColor Yellow
docker stop $VictimContainer | Out-Null
Write-Host "  -> Container '$VictimContainer' da bi dung! Dang quan sat Load Balancer chuyen mach..." -ForegroundColor Yellow

$FailedRequests = 0
for ($i = 11; $i -le 25; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-RestMethod -Uri "${TargetUrl}?r=$i" -Method Get -TimeoutSec 3
        $sw.Stop()
        $ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        Write-Host ("  #{0:D2} | HTTP 200 | {1,6} ms | Node: {2} (Failover Active)" -f $i, $ms, $resp.node_id) -ForegroundColor Cyan
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),200,$ms,$($resp.node_id),During_Node1_Down" | Add-Content -Path $LogFile
    } catch {
        $sw.Stop()
        $FailedRequests++
        Write-Host ("  #{0:D2} | HTTP 5xx | {1,6} ms | Dang chuyen mach upstream..." -f $i, $sw.Elapsed.TotalMilliseconds) -ForegroundColor Red
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),502,$($sw.Elapsed.TotalMilliseconds),ERROR,During_Node1_Down" | Add-Content -Path $LogFile
    }
    Start-Sleep -Milliseconds 150
}

Write-Host "`n[Giai doan 3] KHOI PHUC: Khoi dong lai container '$VictimContainer'..." -ForegroundColor Green
docker start $VictimContainer | Out-Null
Start-Sleep -Seconds 3
docker exec ecom-v2-lb nginx -s reload 2>$null

for ($i = 26; $i -le 35; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-RestMethod -Uri "${TargetUrl}?r=$i" -Method Get -TimeoutSec 3
        $sw.Stop()
        $ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        Write-Host ("  #{0:D2} | HTTP 200 | {1,6} ms | Node: {2}" -f $i, $ms, $resp.node_id) -ForegroundColor Green
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),200,$ms,$($resp.node_id),Recovered_Both_Nodes" | Add-Content -Path $LogFile
    } catch {
        $sw.Stop()
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),502,$($sw.Elapsed.TotalMilliseconds),ERROR,Recovered_Both_Nodes" | Add-Content -Path $LogFile
    }
    Start-Sleep -Milliseconds 150
}

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host " KET QUA THUC NGHIEM FAILOVER:" -ForegroundColor Cyan
Write-Host " - So request bi gian doan khi dung 1 ban sao: $FailedRequests / 15"
Write-Host " - Nhat ky chi tiet da luu tai: $LogFile"
Write-Host "==================================================================" -ForegroundColor Cyan
