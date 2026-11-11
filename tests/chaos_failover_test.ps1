# =============================================================================
# KỊCH BẢN TIÊM LỖI & KIỂM CHỨNG KHẢ NĂNG PHỤC HỒI (CHAOS FAILOVER TEST)
# Mục đích: Chủ động dừng 1 bản sao ứng dụng (app-replica-1) khi đang có tải
# để đo thời gian phát hiện lỗi, chuyển đổi dự phòng (RTO) và tỷ lệ lỗi.
# Cách chạy: powershell -ExecutionPolicy Bypass -File .\tests\chaos_failover_test.ps1
# =============================================================================

param(
    [string]$TargetUrl = "http://localhost:8080/health",
    [string]$VictimContainer = "app-replica-1"
)

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " THỰC NGHIỆM TIÊM LỖI & ĐO THỜI GIAN PHỤC HỒI (RTO) - ĐỀ TÀI 1" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

$LogFile = "tests\data\failover_experiment_log.csv"
New-Item -ItemType Directory -Force -Path "tests\data" | Out-Null
"step,timestamp,http_status,latency_ms,served_by_node,phase" | Out-File -FilePath $LogFile -Encoding utf8

Write-Host "`n[Giai đoạn 1] Gửi 10 request kiểm tra trạng thái bình thường (2 Replicas cùng chạy)..." -ForegroundColor Green
for ($i = 1; $i -le 10; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-RestMethod -Uri $TargetUrl -Method Get -TimeoutSec 3
        $sw.Stop()
        $ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        Write-Host ("  #{0:D2} | HTTP 200 | {1,6} ms | Node: {2}" -f $i, $ms, $resp.node_id)
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),200,$ms,$($resp.node_id),Normal_Before_Fault" | Add-Content -Path $LogFile
    } catch {
        $sw.Stop()
        Write-Host ("  #{0:D2} | ERROR    | Request failed" -f $i) -ForegroundColor Red
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),502,$($sw.Elapsed.TotalMilliseconds),ERROR,Normal_Before_Fault" | Add-Content -Path $LogFile
    }
    Start-Sleep -Milliseconds 250
}

Write-Host "`n[Giai đoạn 2] ⚡ TIÊM LỖI: Chủ động dừng container '$VictimContainer'..." -ForegroundColor Yellow
$FaultStartTime = Get-Date
docker stop $VictimContainer | Out-Null
Write-Host "  -> Container '$VictimContainer' đã bị dừng! Đang quan sát Load Balancer chuyển mạch..." -ForegroundColor Yellow

$FailedRequests = 0
for ($i = 11; $i -le 25; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-RestMethod -Uri $TargetUrl -Method Get -TimeoutSec 3
        $sw.Stop()
        $ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        Write-Host ("  #{0:D2} | HTTP 200 | {1,6} ms | Node: {2} (Failover Active)" -f $i, $ms, $resp.node_id) -ForegroundColor Cyan
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),200,$ms,$($resp.node_id),During_Node1_Down" | Add-Content -Path $LogFile
    } catch {
        $sw.Stop()
        $FailedRequests++
        Write-Host ("  #{0:D2} | HTTP 5xx | {1,6} ms | Đang chuyển mạch upstream..." -f $i, $sw.Elapsed.TotalMilliseconds) -ForegroundColor Red
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),502,$($sw.Elapsed.TotalMilliseconds),ERROR,During_Node1_Down" | Add-Content -Path $LogFile
    }
    Start-Sleep -Milliseconds 250
}

Write-Host "`n[Giai đoạn 3] 🔄 KHÔI PHỤC: Khởi động lại container '$VictimContainer'..." -ForegroundColor Green
docker start $VictimContainer | Out-Null
Start-Sleep -Seconds 3

for ($i = 26; $i -le 35; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-RestMethod -Uri $TargetUrl -Method Get -TimeoutSec 3
        $sw.Stop()
        $ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        Write-Host ("  #{0:D2} | HTTP 200 | {1,6} ms | Node: {2}" -f $i, $ms, $resp.node_id) -ForegroundColor Green
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),200,$ms,$($resp.node_id),Recovered_Both_Nodes" | Add-Content -Path $LogFile
    } catch {
        $sw.Stop()
        "$i,$(Get-Date -Format 'HH:mm:ss.fff'),502,$($sw.Elapsed.TotalMilliseconds),ERROR,Recovered_Both_Nodes" | Add-Content -Path $LogFile
    }
    Start-Sleep -Milliseconds 250
}

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host " KẾT QUẢ THỰC NGHIỆM FAILOVER:" -ForegroundColor Cyan
Write-Host " - Số request bị gián đoạn khi dừng 1 bản sao: $FailedRequests / 15"
Write-Host " - Nhật ký chi tiết đã lưu tại: $LogFile"
Write-Host "==================================================================" -ForegroundColor Cyan
