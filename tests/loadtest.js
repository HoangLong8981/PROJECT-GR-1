// =============================================================================
// KỊCH BẢN KIỂM THỬ TẢI 3 GIAI ĐOẠN BẰNG K6 (NORMAL -> PEAK -> SPIKE FLASH SALE)
// Cách chạy:
//   k6 run -e TARGET_URL=http://localhost:8080 -e ARCH_LABEL=V2 tests/loadtest.js
// =============================================================================

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('http_5xx_error_rate');
const orderLatency = new Trend('order_creation_latency_ms');

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8080';
const ARCH_LABEL = __ENV.ARCH_LABEL || 'V2-Well-Architected';

export const options = {
  scenarios: {
    ecommerce_three_tier_workload: {
      executor: 'ramping-vus',
      startVUs: 5,
      stages: [
        // Mức 1: Tải bình thường (Normal Load)
        { duration: '20s', target: 30 },
        // Mức 2: Tải cao điểm (Peak Load)
        { duration: '25s', target: 100 },
        // Mức 3: Tải tăng đột biến (Flash Sale Spike)
        { duration: '15s', target: 250 },
        // Hạ nhiệt (Scale-down / Cooldown)
        { duration: '10s', target: 10 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    // Ngưỡng chấp nhận NFR theo Mục 3.1.3 của Báo cáo
    http_req_duration: ['p(50)<100', 'p(95)<300'],
    http_5xx_error_rate: ['rate<0.01'],
  },
};

export default function () {
  // 1. Luồng người dùng xem trang danh sách sản phẩm (70% lưu lượng)
  const listRes = http.get(`${BASE_URL}/api/products?limit=12`, {
    tags: { endpoint: 'list_products', arch: ARCH_LABEL },
  });

  const listOk = check(listRes, {
    'GET /api/products status 200': (r) => r.status === 200,
    'Có header X-Served-By': (r) => r.headers['X-Served-By'] !== undefined,
  });
  errorRate.add(listRes.status >= 500);

  // 2. Luồng người dùng xem chi tiết 1 sản phẩm ngẫu nhiên từ 1..100
  const randomProductId = Math.floor(Math.random() * 100) + 1;
  const detailRes = http.get(`${BASE_URL}/api/products/${randomProductId}`, {
    tags: { endpoint: 'product_detail', arch: ARCH_LABEL },
  });
  check(detailRes, {
    'GET /api/products/{id} status 200': (r) => r.status === 200,
  });
  errorRate.add(detailRes.status >= 500);

  // 3. Luồng người dùng đặt hàng (25% xác suất chuyển đổi thành đơn hàng)
  if (Math.random() < 0.25) {
    const payload = JSON.stringify({
      customer_name: `KhachHang_VU_${__VU}`,
      product_id: randomProductId,
      quantity: 1,
    });
    const params = {
      headers: { 'Content-Type': 'application/json' },
      tags: { endpoint: 'create_order', arch: ARCH_LABEL },
    };

    const t0 = Date.now();
    const orderRes = http.post(`${BASE_URL}/api/orders`, payload, params);
    orderLatency.add(Date.now() - t0);

    check(orderRes, {
      'POST /api/orders status 201': (r) => r.status === 201,
    });
    errorRate.add(orderRes.status >= 500);
  }

  sleep(0.2);
}

export function handleSummary(data) {
  const outFile = `tests/data/k6_summary_${ARCH_LABEL}.json`;
  return {
    [outFile]: JSON.stringify(data, null, 2),
  };
}
