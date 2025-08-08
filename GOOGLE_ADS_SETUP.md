# Quickstart 5 phút (Production)

1) Bật Google Ads API + OAuth trên Google Cloud
   - Console → APIs & Services → Library → enable “Google Ads API”
   - OAuth consent screen: External → thêm scope `https://www.googleapis.com/auth/adwords` → Publish

2) Tạo OAuth Client (Desktop app)
   - Credentials → Create credentials → OAuth client ID → Desktop app
   - Lưu `Client ID`, `Client Secret`

3) Tạo Refresh Token (ổn định, lâu dài)
   - Cài lib: `pip install google-ads`
   - Chạy:
     ```
     google-ads oauth2 \
       --client_id "<CLIENT_ID>" \
       --client_secret "<CLIENT_SECRET>" \
       --scopes "https://www.googleapis.com/auth/adwords"
     ```
   - Đăng nhập và chấp thuận → nhận `refresh_token`

4) Lấy Developer Token (Production)
   - Google Ads UI → Tools & Settings → API Center → Apply → Request Standard access
   - Nếu tài khoản cá nhân không xin được, tạo MCC (miễn phí), link tài khoản vào MCC và xin token từ MCC (vẫn dùng được cho tài khoản đơn lẻ)

5) Lấy Customer ID
   - Dạng `123-456-7890` → nhập vào tool là `1234567890`

6) Nhập vào Store Manager của tool
   - Customer ID, Developer Token, Client ID, Client Secret, Refresh Token → bấm “Thêm Store”

7) Kiểm tra chạy thật
   - Mở “📢 Google Ads Analyzer” → chọn store → Phân tích
   - Thấy impressions/clicks/cost là OK (không phải dữ liệu test)

8) Deploy an toàn (Streamlit Cloud)
   - Lưu các giá trị nhạy cảm vào Secrets, không commit lên repo

Lỗi nhanh cần nhớ: `REQUEST_NOT_PERMITTED` (token vẫn Test), `PERMISSION_DENIED` (user không có quyền vào account), `invalid_grant` (sai client/secret hoặc app chưa publish).

---

# Hướng dẫn lấy thông số Google Ads dùng thật (Production)

Tool cần 5 thông số để gọi Google Ads API ổn định, lâu dài:
- Google Ads Customer ID: ID tài khoản quảng cáo (10 số, bỏ dấu gạch)
- Developer Token: token API của tài khoản (đã được duyệt dùng Production)
- Client ID: OAuth 2.0 Client ID (tạo trên Google Cloud)
- Client Secret: OAuth 2.0 Client Secret (Google Cloud)
- Refresh Token: token làm mới, giúp gọi API không cần đăng nhập lại (bền vững)

Bạn có thể dùng cho 1 tài khoản lẻ hoặc tài khoản MCC (quản lý nhiều khách hàng). Chi tiết dưới đây.

---

## A) Khác biệt Test vs Production (quan trọng)
- Basic/Test access: chỉ gọi được dữ liệu từ tài khoản “test” → KHÔNG dùng được cho tài khoản thật.
- Standard/Production access: gọi được dữ liệu tài khoản thật → BẮT BUỘC để dùng trong thực tế.

Muốn Go-Live: Developer token phải được duyệt Standard access trong Google Ads API Center.

---

## B) Checklist đi Live (Standard access)
1) Có Google Ads account đang chạy thật (hoặc MCC quản lý tài khoản thật)
2) Có website/app hợp lệ, chính sách quyền riêng tư
3) Mô tả use case rõ ràng khi apply API (đo lường hiệu quả, báo cáo nội bộ, tối ưu bidding…)
4) Bật Google Ads API trong Google Cloud & tạo OAuth consent screen
5) Tạo OAuth Client (Client ID/Secret)
6) Xin Developer Token ở API Center → sau khi có Basic, tiếp tục yêu cầu Standard (Production)
7) Tạo Refresh token từ Client ID/Secret (scope adwords)

Thời gian duyệt Standard thường 1–7 ngày (tuỳ hồ sơ).

---

## C) Bật API và tạo OAuth trên Google Cloud
1) Vào `https://console.cloud.google.com/` → chọn/tạo Project
2) APIs & Services → Library → bật “Google Ads API”
3) OAuth consent screen:
   - User type: External
   - Thêm scope: `https://www.googleapis.com/auth/adwords`
   - Điền thông tin app; xuất bản (Publish) nếu dùng ngoài phạm vi test
4) Credentials → Create Credentials → OAuth client ID:
   - Chọn loại “Desktop app” (dễ tạo refresh token)
   - Ghi lại: Client ID, Client Secret

Gợi ý: Có thể thêm một OAuth client “Web application” cho app production, nhưng tạo refresh token dùng “Desktop app” là nhanh nhất.

---

## D) Lấy Developer Token ở Google Ads (Production)
1) Đăng nhập `https://ads.google.com/`
2) Tools & Settings (cờ lê) → “API Center”
3) Apply for API access → nhận Developer Token (ban đầu Basic/Test)
4) Bấm “Request Standard access” để dùng tài khoản thật
   - Trả lời câu hỏi về use case, luồng dữ liệu, bảo mật dữ liệu người dùng, chính sách quyền riêng tư
   - Đảm bảo website hợp lệ, có trang Privacy Policy

Khi Standard được duyệt, token dùng được với tài khoản thật.

---

## E) Lấy Customer ID
- Xem ở góc phải Google Ads UI hoặc phần Account: dạng `123-456-7890`
- Nhập vào tool là `1234567890` (bỏ dấu '-')
- Nếu dùng MCC: Customer ID là tài khoản con bạn muốn truy vấn; MCC ID có thể dùng làm `login_customer_id` (tham khảo phần MCC).

---

## F) Tạo Refresh Token (ổn định, lâu dài)
Cách nhanh bằng CLI (yêu cầu `pip install google-ads`):

```
google-ads oauth2 \
  --client_id "<CLIENT_ID>" \
  --client_secret "<CLIENT_SECRET>" \
  --scopes "https://www.googleapis.com/auth/adwords"
```
- Trình duyệt mở ra → đăng nhập Google có quyền vào tài khoản Ads → chấp thuận → CLI in `refresh_token`.

Nếu lệnh `google-ads` không chạy, dùng Python module:
```
python -m google.ads.googleads.oauth2 \
  --client_id "<CLIENT_ID>" \
  --client_secret "<CLIENT_SECRET>" \
  --scopes "https://www.googleapis.com/auth/adwords"
```

Lưu ý ổn định:
- Refresh token không hết hạn theo thời gian, chỉ mất hiệu lực khi thu hồi quyền hoặc thay đổi OAuth consent.
- Không chia sẻ/public; lưu trong Secrets (xem phần H).

---

## G) Case dùng MCC (quản lý nhiều tài khoản)
- Developer token nên thuộc MCC.
- Khi gọi API, bạn có thể chỉ định:
  - `login_customer_id`: ID MCC (không có dấu '-')
  - `customer_id`: ID tài khoản con cần truy vấn
- Yêu cầu: MCC phải có quyền truy cập tài khoản con, và điều khoản chính sách phù hợp.

Ví dụ cấu hình YAML (tham khảo):
```
developer_token: "<DEVELOPER_TOKEN>"
client_id: "<CLIENT_ID>"
client_secret: "<CLIENT_SECRET>"
refresh_token: "<REFRESH_TOKEN>"
use_proto_plus: true
# Tùy chọn nếu dùng MCC:
# login_customer_id: "1234567890"
```

Tool hiện chưa yêu cầu trường `login_customer_id`. Nếu cần, hãy báo để bật tùy chọn này trong UI.

---

## H) Bảo mật & deploy (Streamlit Cloud)
- Tuyệt đối không commit Client Secret/Refresh Token lên repo public
- Vào Streamlit Cloud → App → Settings → Secrets, lưu:
```
GOOGLE_ADS_DEVELOPER_TOKEN="..."
GOOGLE_ADS_CLIENT_ID="..."
GOOGLE_ADS_CLIENT_SECRET="..."
GOOGLE_ADS_REFRESH_TOKEN="..."
```
- Trong code đọc bằng `st.secrets["GOOGLE_ADS_DEVELOPER_TOKEN"]` …
- Local: dùng `.env` hoặc nhập trực tiếp trong Store Manager (chỉ lưu local JSON)

---

## I) Kiểm tra nhanh (sanity check)
Chạy truy vấn GAQL đơn giản để kiểm tra token & quyền:
```python
from google.ads.googleads.client import GoogleAdsClient

config = {
    "developer_token": "<DEV_TOKEN>",
    "client_id": "<CLIENT_ID>",
    "client_secret": "<CLIENT_SECRET>",
    "refresh_token": "<REFRESH_TOKEN>",
    "use_proto_plus": True,
}
client = GoogleAdsClient.load_from_dict(config)
svc = client.get_service("GoogleAdsService")
query = """
  SELECT campaign.id, campaign.name, metrics.impressions, metrics.clicks
  FROM campaign
  WHERE segments.date DURING LAST_7_DAYS
  LIMIT 5
"""
resp = svc.search(customer_id="1234567890", query=query)
for row in resp:
    print(row.campaign.id, row.campaign.name, row.metrics.impressions, row.metrics.clicks)
```
Nếu ra dữ liệu → cấu hình OK để dùng Production.

---

## J) Lỗi thường gặp & cách xử lý nhanh
- `REQUEST_NOT_PERMITTED` / không có dữ liệu thật: Developer token chỉ ở Basic/Test → cần Standard access.
- `PERMISSION_DENIED`: Tài khoản Google tạo refresh token không có quyền vào Customer ID; hoặc chưa chỉ định đúng Customer ID con (case MCC).
- `invalid_grant` khi tạo refresh token: sai Client ID/Secret, app chưa publish, chọn nhầm tài khoản Google.
- Dữ liệu rỗng: account chưa có traffic gần đây; GAQL lọc quá hẹp; hoặc vẫn đang ở Test access.

---

## K) Nhập vào Tool
Trong `🏪 Store Manager` → `📢 Google Ads Configuration` nhập:
- Google Ads Customer ID: 10 số, không có `-`
- Developer Token
- Client ID
- Client Secret
- Refresh Token
Lưu store → mở `📢 Google Ads Analyzer` hoặc `📊 GA4 + Ads Analyzer` để chạy dùng thật.

Cần hỗ trợ bật `login_customer_id` (MCC) trong UI? Hãy nhắn, tôi sẽ thêm ngay.
