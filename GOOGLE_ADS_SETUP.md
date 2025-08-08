### Hướng dẫn lấy thông số Google Ads (Customer ID, Developer Token, Client ID, Client Secret, Refresh Token)

Để sử dụng mục phân tích Google Ads trong tool, bạn cần 5 thông số:
- **Google Ads Customer ID**: ID tài khoản quảng cáo (10 số, bỏ dấu gạch)
- **Developer Token**: Token API của tài khoản (lấy trong Google Ads UI)
- **Client ID**: OAuth 2.0 Client ID (Google Cloud)
- **Client Secret**: OAuth 2.0 Client Secret (Google Cloud)
- **Refresh Token**: Token làm mới để gọi API không cần đăng nhập lại

---

### 1) Tạo/O sử dụng Project trên Google Cloud
- Vào `https://console.cloud.google.com/`
- Tạo Project mới hoặc chọn Project hiện có
- Vào `APIs & Services` → `Library` → bật API: `Google Ads API`

---

### 2) Tạo OAuth Consent Screen
- Vào `APIs & Services` → `OAuth consent screen`
- User type: `External` (phổ biến) → Create
- App name: đặt tên tùy ý, email hỗ trợ
- Scopes: thêm scope `https://www.googleapis.com/auth/adwords`
- Publish app (nếu cần dùng ngoài phạm vi test)

---

### 3) Tạo OAuth 2.0 Credentials (Client ID/Secret)
- Vào `APIs & Services` → `Credentials`
- `Create Credentials` → `OAuth client ID`
- Application type: chọn `Desktop app` (dễ lấy refresh token)
- Sau khi tạo, ghi lại: `Client ID`, `Client Secret`

Lưu ý: Bạn có thể tạo thêm một OAuth Client cho server nếu muốn, nhưng để lấy `refresh_token` nhanh nhất nên dùng kiểu `Desktop app`.

---

### 4) Lấy Developer Token trong Google Ads
- Đăng nhập Google Ads: `https://ads.google.com/`
- Trên thanh công cụ: Tools & Settings (biểu tượng cờ lê) → `API Center`
- Nếu chưa đăng ký, nhấn “Apply for API access” → Developer token sẽ ở trạng thái `Pending/Test`
- Sau khi được duyệt Production, token sẽ dùng được với tài khoản thật. Ở chế độ Test, chỉ dùng được với tài khoản test.
- Sao chép `Developer Token` (dạng chữ + số)

---

### 5) Lấy Google Ads Customer ID
- Trong Google Ads UI, nhìn góc trên phải hoặc phần Account, sẽ thấy ID dạng `123-456-7890`
- Bỏ dấu `-` để nhập vào tool thành `1234567890`
- Nếu dùng tài khoản MCC (manager), đây là ID tài khoản con bạn muốn truy vấn

Tuỳ chọn (Manager Accounts): `login-customer-id` là ID MCC bao trùm. Tool hiện không yêu cầu trường này, nhưng nếu cần, có thể cập nhật sau.

---

### 6) Tạo Refresh Token (cách đơn giản bằng CLI)
Yêu cầu: đã `pip install google-ads`.

Chạy lệnh sau (Windows PowerShell/CMD/Mac/Linux):
```
google-ads oauth2 \
  --client_id "<CLIENT_ID>" \
  --client_secret "<CLIENT_SECRET>" \
  --scopes "https://www.googleapis.com/auth/adwords"
```
- Trình duyệt sẽ mở, đăng nhập Google, chọn tài khoản có quyền truy cập Ads
- Sau khi chấp thuận, CLI sẽ in ra `refresh_token`

Nếu lệnh `google-ads` không nhận, thử chạy dạng Python module:
```
python -m google.ads.googleads.oauth2 \
  --client_id "<CLIENT_ID>" \
  --client_secret "<CLIENT_SECRET>" \
  --scopes "https://www.googleapis.com/auth/adwords"
```

---

### 7) Ví dụ cấu hình `google-ads.yaml` (tham khảo)
Tool sẽ tự tạo file tạm thời khi gọi API, nhưng đây là ví dụ để bạn kiểm tra nhanh:
```
developer_token: "<DEVELOPER_TOKEN>"
client_id: "<CLIENT_ID>"
client_secret: "<CLIENT_SECRET>"
refresh_token: "<REFRESH_TOKEN>"
use_proto_plus: true
```
Nếu dùng manager account và cần chỉ định MCC:
```
login_customer_id: "1234567890"
```

---

### 8) Nhập thông số vào Store Manager của Tool
Trong trang `🏪 Store Manager` → mục `📢 Google Ads Configuration` nhập:
- Google Ads Customer ID → `customer_id` (10 số, không có `-`)
- Developer Token → `developer_token`
- Client ID → `client_id`
- Client Secret → `client_secret`
- Refresh Token → `refresh_token`
Lưu store là xong.

---

### 9) Lỗi thường gặp & cách xử lý
- `PERMISSION_DENIED` / `REQUEST_NOT_PERMITTED`:
  - Developer token chưa được duyệt hoặc đang ở chế độ Test nhưng bạn gọi dữ liệu tài khoản thật
  - Tài khoản Google bạn dùng để lấy refresh token không có quyền trên Customer ID
- `invalid_grant` khi tạo refresh token:
  - Sai `client_id/client_secret`, app chưa publish/verify, hoặc dùng tài khoản Google khác
- Dữ liệu rỗng khi ở chế độ Test:
  - Tạo tài khoản test trong Google Ads Sandbox hoặc chuyển Developer token sang Production (được duyệt)

---

### 10) Bảo mật khi deploy
- Trên Streamlit Cloud, đưa các giá trị nhạy cảm vào `Secrets` thay vì hard-code
- Không commit `refresh_token`/`client_secret` lên Git công khai

---

### Tài liệu tham khảo
- Google Ads API Docs: `https://developers.google.com/google-ads/api/docs/start`
- OAuth2 Guide: `https://developers.google.com/google-ads/api/docs/oauth/overview`
- google-ads Python library: `https://github.com/googleads/google-ads-python`
