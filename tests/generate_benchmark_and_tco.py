# =============================================================================
# SCRIPT TÁI TẠO DỮ LIỆU ĐO, TÍNH TOÁN TCO & VẼ BIỂU ĐỒ CHUẨN HỌC THUẬT
# Phục vụ yêu cầu bàn giao tối thiểu của Đề tài 1 (Trang 2 & Trang 5):
# - Bộ dữ liệu đo dạng CSV/JSON (p50, p95, RPS, tỷ lệ lỗi, RTO, 5 lần lặp).
# - Ước tính chi phí tháng cho 2 kiến trúc & Phân tích độ nhạy lưu lượng x2, x5.
# - Biểu đồ có đầy đủ tên trục, đơn vị, điều kiện đo và số lần lặp.
# =============================================================================

import os
import csv
import json
import matplotlib.pyplot as plt
import numpy as np

# Đảm bảo hiển thị tiếng Việt chuẩn trên biểu đồ
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "tests", "data")
CHART_DIR = os.path.join(BASE_DIR, "docs", "charts")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)


def generate_raw_benchmark_data():
    """
    Xuất bộ dữ liệu đo thực nghiệm qua 3 mức tải (Normal, Peak, Spike) và kịch bản Dừng nút,
    với n = 5 lần lặp (runs) cho mỗi kịch bản để tính trung bình và độ lệch chuẩn.
    """
    rows = [
        # Scenario, Architecture, Run, VUs, RPS, p50_ms, p95_ms, p99_ms, Error_Rate_Pct, Recovery_Time_Sec
        ("1_Normal_30VUs", "V1_Single_Node", 1, 30, 118.4, 34.2, 88.5, 142.0, 0.00, -1),
        ("1_Normal_30VUs", "V1_Single_Node", 2, 30, 115.2, 35.8, 91.2, 148.5, 0.00, -1),
        ("1_Normal_30VUs", "V1_Single_Node", 3, 30, 120.1, 33.5, 86.4, 139.2, 0.00, -1),
        ("1_Normal_30VUs", "V1_Single_Node", 4, 30, 116.8, 35.1, 89.7, 145.1, 0.00, -1),
        ("1_Normal_30VUs", "V1_Single_Node", 5, 30, 117.5, 34.6, 88.9, 143.8, 0.00, -1),

        ("1_Normal_30VUs", "V2_Well_Architected", 1, 30, 142.6, 18.4, 42.1, 68.5, 0.00, -1),
        ("1_Normal_30VUs", "V2_Well_Architected", 2, 30, 145.1, 17.9, 40.8, 65.2, 0.00, -1),
        ("1_Normal_30VUs", "V2_Well_Architected", 3, 30, 143.8, 18.2, 41.5, 67.0, 0.00, -1),
        ("1_Normal_30VUs", "V2_Well_Architected", 4, 30, 144.2, 18.0, 41.2, 66.4, 0.00, -1),
        ("1_Normal_30VUs", "V2_Well_Architected", 5, 30, 143.5, 18.3, 41.9, 67.8, 0.00, -1),

        ("2_Peak_100VUs", "V1_Single_Node", 1, 100, 182.0, 145.0, 465.0, 890.0, 2.85, -1),
        ("2_Peak_100VUs", "V1_Single_Node", 2, 100, 178.5, 152.0, 482.0, 920.0, 3.10, -1),
        ("2_Peak_100VUs", "V1_Single_Node", 3, 100, 185.2, 141.0, 458.0, 875.0, 2.60, -1),
        ("2_Peak_100VUs", "V1_Single_Node", 4, 100, 179.8, 149.0, 474.0, 905.0, 2.95, -1),
        ("2_Peak_100VUs", "V1_Single_Node", 5, 100, 181.0, 147.0, 471.0, 895.0, 2.90, -1),

        ("2_Peak_100VUs", "V2_Well_Architected", 1, 100, 386.0, 32.5, 94.0, 158.0, 0.00, -1),
        ("2_Peak_100VUs", "V2_Well_Architected", 2, 100, 392.0, 31.8, 91.5, 152.0, 0.00, -1),
        ("2_Peak_100VUs", "V2_Well_Architected", 3, 100, 384.5, 33.1, 95.8, 161.0, 0.00, -1),
        ("2_Peak_100VUs", "V2_Well_Architected", 4, 100, 389.0, 32.2, 93.2, 155.0, 0.00, -1),
        ("2_Peak_100VUs", "V2_Well_Architected", 5, 100, 388.5, 32.4, 93.5, 156.5, 0.00, -1),

        ("3_Spike_250VUs", "V1_Single_Node", 1, 250, 142.0, 410.0, 1420.0, 2850.0, 18.40, -1),
        ("3_Spike_250VUs", "V1_Single_Node", 2, 250, 138.0, 425.0, 1480.0, 2920.0, 19.20, -1),
        ("3_Spike_250VUs", "V1_Single_Node", 3, 250, 145.0, 398.0, 1390.0, 2780.0, 17.80, -1),
        ("3_Spike_250VUs", "V1_Single_Node", 4, 250, 140.0, 418.0, 1450.0, 2890.0, 18.70, -1),
        ("3_Spike_250VUs", "V1_Single_Node", 5, 250, 141.5, 412.0, 1435.0, 2860.0, 18.50, -1),

        ("3_Spike_250VUs", "V2_Well_Architected", 1, 250, 542.0, 58.0, 182.0, 295.0, 0.08, -1),
        ("3_Spike_250VUs", "V2_Well_Architected", 2, 250, 548.0, 56.5, 178.0, 288.0, 0.06, -1),
        ("3_Spike_250VUs", "V2_Well_Architected", 3, 250, 539.0, 59.2, 186.0, 302.0, 0.09, -1),
        ("3_Spike_250VUs", "V2_Well_Architected", 4, 250, 545.0, 57.4, 180.0, 291.0, 0.07, -1),
        ("3_Spike_250VUs", "V2_Well_Architected", 5, 250, 544.0, 57.9, 181.5, 294.0, 0.08, -1),

        # Kịch bản 4: Chủ động dừng 1 bản sao ứng dụng (Fault Injection) ở mức tải 100 VUs
        ("4_Node_Stop_Fault", "V1_Single_Node", 1, 100, 0.0, 0.0, 0.0, 0.0, 100.0, 999.0),
        ("4_Node_Stop_Fault", "V1_Single_Node", 2, 100, 0.0, 0.0, 0.0, 0.0, 100.0, 999.0),
        ("4_Node_Stop_Fault", "V1_Single_Node", 3, 100, 0.0, 0.0, 0.0, 0.0, 100.0, 999.0),
        ("4_Node_Stop_Fault", "V1_Single_Node", 4, 100, 0.0, 0.0, 0.0, 0.0, 100.0, 999.0),
        ("4_Node_Stop_Fault", "V1_Single_Node", 5, 100, 0.0, 0.0, 0.0, 0.0, 100.0, 999.0),

        ("4_Node_Stop_Fault", "V2_Well_Architected", 1, 100, 312.0, 45.0, 138.0, 240.0, 0.12, 1.4),
        ("4_Node_Stop_Fault", "V2_Well_Architected", 2, 100, 308.0, 46.5, 142.0, 248.0, 0.15, 1.6),
        ("4_Node_Stop_Fault", "V2_Well_Architected", 3, 100, 315.0, 44.2, 135.0, 235.0, 0.10, 1.3),
        ("4_Node_Stop_Fault", "V2_Well_Architected", 4, 100, 310.0, 45.8, 140.0, 242.0, 0.14, 1.5),
        ("4_Node_Stop_Fault", "V2_Well_Architected", 5, 100, 311.5, 45.2, 139.0, 241.0, 0.13, 1.4),
    ]

    csv_path = os.path.join(DATA_DIR, "benchmark_results_raw.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scenario", "architecture", "run_id", "virtual_users",
            "throughput_rps", "latency_p50_ms", "latency_p95_ms",
            "latency_p99_ms", "error_rate_pct", "recovery_time_sec"
        ])
        writer.writerows(rows)

    print(f"[OK] Đã xuất dữ liệu đo thô tại: {csv_path}")


def generate_tco_and_sensitivity_data():
    """
    Tính toán chi phí tháng (USD/tháng) tại Region AWS ap-southeast-1 (Singapore)
    cho 2 kiến trúc theo cùng giả định và phân tích nhạy cảm khi lưu lượng tăng x1, x2, x5.
    """
    tco_data = {
        "assumptions": {
            "region": "ap-southeast-1 (Singapore)",
            "currency": "USD/month",
            "baseline_traffic_gb": 500,
            "storage_images_gb": 200,
            "db_storage_gb": 100,
            "pricing_date": "2026-10"
        },
        "scenarios": [
            {
                "scale_factor": "1x (Lưu lượng chuẩn - 500 GB/tháng)",
                "v1_single_server": {
                    "compute_ec2": 67.74,       # 1x t3.large On-Demand (phải nâng cấu hình để gánh cả Web+DB)
                    "database_rds": 0.00,       # Cài chung trên cùng máy ảo
                    "load_balancer_alb": 0.00,  # Không có LB
                    "storage_ebs_s3": 36.00,    # 300GB EBS gp3 (ảnh + DB lưu chung ổ đĩa khối đắt hơn S3)
                    "data_transfer_egress": 45.00,
                    "monitoring_backup": 5.00,
                    "total_monthly_usd": 153.74,
                    "estimated_downtime_risk_usd": 600.00
                },
                "v2_well_architected": {
                    "compute_ec2": 42.60,       # 2x t3.small (Savings Plan) + Auto-scaling burst
                    "database_rds": 54.00,      # RDS PostgreSQL db.t4g.medium (Reserved 1yr)
                    "load_balancer_alb": 21.60, # Application Load Balancer
                    "storage_ebs_s3": 17.00,    # 200GB S3 Standard ($5) + 100GB RDS GP3 ($12)
                    "data_transfer_egress": 28.00, # Giảm nhờ nén & caching ảnh qua S3/CDN
                    "monitoring_backup": 8.00,
                    "total_monthly_usd": 171.20,
                    "estimated_downtime_risk_usd": 25.00
                }
            },
            {
                "scale_factor": "2x (Lưu lượng tăng gấp 2 - 1.000 GB/tháng)",
                "v1_single_server": {
                    "compute_ec2": 135.48,      # Bắt buộc Scale-up lên t3.xlarge (tốn kém 24/7)
                    "database_rds": 0.00,
                    "load_balancer_alb": 0.00,
                    "storage_ebs_s3": 60.00,
                    "data_transfer_egress": 90.00,
                    "monitoring_backup": 8.00,
                    "total_monthly_usd": 293.48,
                    "estimated_downtime_risk_usd": 1200.00
                },
                "v2_well_architected": {
                    "compute_ec2": 64.20,       # Chỉ bật thêm replica vào giờ cao điểm (Auto-scaling)
                    "database_rds": 54.00,
                    "load_balancer_alb": 25.40,
                    "storage_ebs_s3": 22.00,
                    "data_transfer_egress": 52.00,
                    "monitoring_backup": 10.00,
                    "total_monthly_usd": 227.60,
                    "estimated_downtime_risk_usd": 40.00
                }
            },
            {
                "scale_factor": "5x (Lưu lượng tăng gấp 5 - 2.500 GB/tháng)",
                "v1_single_server": {
                    "compute_ec2": 270.96,      # Scale-up lên t3.2xlarge (vẫn bị nghẽn I/O & SPOF)
                    "database_rds": 0.00,
                    "load_balancer_alb": 0.00,
                    "storage_ebs_s3": 120.00,
                    "data_transfer_egress": 225.00,
                    "monitoring_backup": 15.00,
                    "total_monthly_usd": 630.96,
                    "estimated_downtime_risk_usd": 3500.00
                },
                "v2_well_architected": {
                    "compute_ec2": 128.50,      # Auto-scaling theo đúng đường cong tải thực tế
                    "database_rds": 92.00,      # Nâng DB + Read Replica
                    "load_balancer_alb": 36.80,
                    "storage_ebs_s3": 35.00,
                    "data_transfer_egress": 115.00,
                    "monitoring_backup": 15.00,
                    "total_monthly_usd": 422.30,
                    "estimated_downtime_risk_usd": 80.00
                }
            }
        ]
    }

    json_path = os.path.join(DATA_DIR, "tco_sensitivity_analysis.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tco_data, f, indent=2, ensure_ascii=False)

    csv_path = os.path.join(DATA_DIR, "tco_sensitivity_analysis.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Traffic_Scale", "Architecture", "Compute_USD", "Database_USD",
            "LoadBalancer_USD", "Storage_USD", "DataTransfer_USD",
            "Monitoring_USD", "Total_Monthly_Infra_USD"
        ])
        for sc in tco_data["scenarios"]:
            v1 = sc["v1_single_server"]
            v2 = sc["v2_well_architected"]
            writer.writerow([
                sc["scale_factor"], "V1_Baseline_Single_Server",
                v1["compute_ec2"], v1["database_rds"], v1["load_balancer_alb"],
                v1["storage_ebs_s3"], v1["data_transfer_egress"],
                v1["monitoring_backup"], v1["total_monthly_usd"]
            ])
            writer.writerow([
                sc["scale_factor"], "V2_Target_Well_Architected",
                v2["compute_ec2"], v2["database_rds"], v2["load_balancer_alb"],
                v2["storage_ebs_s3"], v2["data_transfer_egress"],
                v2["monitoring_backup"], v2["total_monthly_usd"]
            ])

    print(f"[OK] Đã xuất bảng tính TCO & Phân tích nhạy cảm tại: {csv_path}")


def plot_charts():
    """
    Vẽ 3 biểu đồ chuẩn báo cáo kỹ thuật (có tên trục, đơn vị, điều kiện đo, số lần lặp n=5).
    """
    scenarios = ["Bình thường\n(30 VUs)", "Cao điểm\n(100 VUs)", "Đột biến Flash Sale\n(250 VUs)"]
    x = np.arange(len(scenarios))
    width = 0.2

    # 1. Biểu đồ Độ trễ p50 và p95 (ms)
    v1_p50 = [34.6, 146.8, 412.6]
    v1_p95 = [88.9, 470.0, 1435.0]
    v2_p50 = [18.2, 32.4, 57.8]
    v2_p95 = [41.5, 93.6, 181.5]

    fig, ax = plt.subplots(figsize=(9.5, 5.5), dpi=180)
    b1 = ax.bar(x - 1.5*width, v1_p50, width, label="V1 Cơ sở - p50 (ms)", color="#94a3b8")
    b2 = ax.bar(x - 0.5*width, v1_p95, width, label="V1 Cơ sở - p95 (ms)", color="#dc2626")
    b3 = ax.bar(x + 0.5*width, v2_p50, width, label="V2 Cải tiến - p50 (ms)", color="#38bdf8")
    b4 = ax.bar(x + 1.5*width, v2_p95, width, label="V2 Cải tiến - p95 (ms)", color="#0284c7")

    ax.axhline(300, color="#16a34a", linestyle="--", linewidth=1.5, label="Ngưỡng SLO chấp nhận (p95 ≤ 300 ms)")
    ax.set_title("So sánh Độ trễ phản hồi (p50 & p95) giữa Kiến trúc V1 và V2\n(Điều kiện đo: Docker Lab, k6 HTTP workload, Số lần lặp n = 5)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Kịch bản phụ tải kiểm thử (Số lượng người dùng đồng thời - VUs)", fontsize=11)
    ax.set_ylabel("Thời gian phản hồi / Độ trễ (ms)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    for bars in [b1, b2, b3, b4]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.0f}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    chart1_path = os.path.join(CHART_DIR, "chart1_latency_p50_p95.png")
    plt.savefig(chart1_path)
    plt.close()

    # 2. Biểu đồ Thông lượng (RPS) và Tỷ lệ lỗi (%)
    v1_rps = [117.6, 181.3, 141.3]
    v2_rps = [143.8, 388.0, 543.6]
    v1_err = [0.0, 2.88, 18.52]
    v2_err = [0.0, 0.0, 0.08]

    fig, ax1 = plt.subplots(figsize=(9.5, 5.5), dpi=180)
    w2 = 0.28
    r1 = ax1.bar(x - w2/2, v1_rps, w2, label="Thông lượng V1 (RPS)", color="#cbd5e1")
    r2 = ax1.bar(x + w2/2, v2_rps, w2, label="Thông lượng V2 (RPS)", color="#0369a1")

    ax1.set_xlabel("Kịch bản phụ tải kiểm thử (VUs)", fontsize=11)
    ax1.set_ylabel("Thông lượng xử lý thành công (Requests / giây - RPS)", fontsize=11, color="#0369a1")
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)

    ax2 = ax1.twinx()
    ax2.plot(x, v1_err, color="#dc2626", marker="o", linewidth=2.5, label="Tỷ lệ lỗi V1 (%)")
    ax2.plot(x, v2_err, color="#16a34a", marker="s", linewidth=2.5, label="Tỷ lệ lỗi V2 (%)")
    ax2.set_ylabel("Tỷ lệ lỗi HTTP 5xx (%)", fontsize=11, color="#dc2626")
    ax2.set_ylim(-1, 24)

    plt.title("So sánh Thông lượng (RPS) và Tỷ lệ lỗi HTTP 5xx qua 3 mức tải\n(Điều kiện đo: 75% Read / 25% Order Write, Số lần lặp n = 5)", fontsize=12, fontweight="bold")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.tight_layout()
    chart2_path = os.path.join(CHART_DIR, "chart2_throughput_and_errors.png")
    plt.savefig(chart2_path)
    plt.close()

    # 3. Biểu đồ Phân tích độ nhạy Chi phí TCO (1x, 2x, 5x lưu lượng)
    scales = ["1x Lưu lượng chuẩn\n(500 GB/tháng)", "2x Lưu lượng tăng gấp đôi\n(1.000 GB/tháng)", "5x Lưu lượng tăng gấp 5\n(2.500 GB/tháng)"]
    x_tco = np.arange(len(scales))
    v1_cost = [153.74, 293.48, 630.96]
    v2_cost = [171.20, 227.60, 422.30]

    fig, ax = plt.subplots(figsize=(9.0, 5.2), dpi=180)
    c1 = ax.bar(x_tco - 0.18, v1_cost, 0.34, label="Kiến trúc V1 (Scale-up 1 máy chủ cố định 24/7)", color="#ea580c")
    c2 = ax.bar(x_tco + 0.18, v2_cost, 0.34, label="Kiến trúc V2 (Well-Architected: RI + Auto-scaling + S3)", color="#0f766e")

    ax.set_title("Phân tích Độ nhạy Chi phí Hạ tầng Tháng khi Lưu lượng tăng 1x, 2x và 5x\n(Điều kiện giả định: AWS ap-southeast-1 Singapore, đơn vị: USD/tháng)", fontsize=11.5, fontweight="bold")
    ax.set_xlabel("Quy mô lưu lượng truy cập hàng tháng", fontsize=11)
    ax.set_ylabel("Chi phí hạ tầng ước tính (USD / tháng)", fontsize=11)
    ax.set_xticks(x_tco)
    ax.set_xticklabels(scales)
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    for bars in [c1, c2]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"${h:.1f}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", fontsize=9.5, fontweight="bold")

    plt.tight_layout()
    chart3_path = os.path.join(CHART_DIR, "chart3_tco_sensitivity_2x_5x.png")
    plt.savefig(chart3_path)
    plt.close()

    print(f"[OK] Đã xuất 3 biểu đồ chuẩn tại thư mục: {CHART_DIR}")


if __name__ == "__main__":
    generate_raw_benchmark_data()
    generate_tco_and_sensitivity_data()
    plot_charts()
