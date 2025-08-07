# 🚀 GA4 Analytics Tool

**Tool phân tích Google Analytics 4 với AI - Dành cho E-commerce**

## 🌟 Tính năng chính

- 📊 **Phân tích GA4** real-time
- 🤖 **AI Insights** với GPT-4o
- 🏪 **Store Manager** - Quản lý nhiều stores
- 📈 **Product Analytics** - Doanh thu, Views, Sales
- 🎯 **Smart Dashboard** - Bảng tổng hợp thông minh

## 🚀 Deploy lên Cloud

### Option 1: Streamlit Cloud (Khuyến nghị)

1. **Fork repository** này về GitHub của bạn
2. **Truy cập:** https://share.streamlit.io/
3. **Connect GitHub** và chọn repository
4. **Deploy** - Tự động!

### Option 2: Heroku

```bash
# Clone repository
git clone <your-repo-url>
cd analytics_tool

# Tạo Heroku app
heroku create your-ga4-analytics-app

# Deploy
git push heroku main
```

### Option 3: Railway

1. **Truy cập:** https://railway.app/
2. **Connect GitHub** repository
3. **Deploy** tự động

## 📋 Cấu hình Environment Variables

### Streamlit Cloud:
- Vào **Settings** → **Secrets**
- Thêm các biến môi trường:

```toml
[secrets]
OPENAI_API_KEY = "your-openai-api-key"
GA4_PROPERTY_ID = "your-ga4-property-id"
```

### Heroku:
```bash
heroku config:set OPENAI_API_KEY=your-openai-api-key
heroku config:set GA4_PROPERTY_ID=your-ga4-property-id
```

## 🛠️ Cài đặt Local

```bash
# Clone repository
git clone <your-repo-url>
cd analytics_tool

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
streamlit run main_app.py
```

## 📁 Cấu trúc Project

```
analytics_tool/
├── main_app.py                    # 🏠 Trang chủ
├── pages/
│   ├── 1_🏪_Store_Manager.py     # 🏪 Quản lý stores
│   └── 2_🔍_GA4_Analyzer.py     # 🔍 Phân tích GA4
├── requirements.txt               # 📦 Dependencies
├── Procfile                      # 🚀 Heroku config
├── runtime.txt                   # 🐍 Python version
├── setup.sh                      # ⚙️ Streamlit config
└── README.md                     # 📖 Documentation
```

## 🔧 Cấu hình GA4

### 1. Tạo Service Account
1. **Truy cập:** https://console.cloud.google.com/
2. **Tạo project** mới hoặc chọn project có sẵn
3. **Enable Google Analytics Data API**
4. **Tạo Service Account** với quyền "Viewer"

### 2. Download Credentials
1. **Tạo key** cho Service Account
2. **Download file JSON**
3. **Upload** vào tool

### 3. Cấu hình GA4 Property
1. **Truy cập GA4** → Admin → Property Settings
2. **Copy Property ID** (dạng số)
3. **Thêm Service Account** vào Property Access

## 🤖 Cấu hình OpenAI

1. **Truy cập:** https://platform.openai.com/account/api-keys
2. **Tạo API key** mới
3. **Nhập vào tool** hoặc cấu hình environment variable

## 📊 Tính năng Dashboard

### 🏪 Store Manager
- ✅ Quản lý nhiều stores
- ✅ Lưu trữ credentials an toàn
- ✅ Chuyển đổi giữa stores

### 🔍 GA4 Analyzer
- ✅ **Metrics cơ bản:** Users, Sessions, Revenue
- ✅ **Product Analytics:** Views, Sales, Revenue
- ✅ **Smart Comparison:** Top Revenue, Sales, Views
- ✅ **AI Insights:** Phân tích tự động với GPT-4o
- ✅ **Error Handling:** Xử lý lỗi robust

## 🎯 Hướng dẫn sử dụng

1. **Chọn store** từ Store Manager
2. **Upload credentials.json** hoặc chọn store đã lưu
3. **Nhập OpenAI API key** (bắt buộc cho AI)
4. **Chọn thời gian** phân tích (1-365 ngày)
5. **Phân tích dữ liệu** và xem kết quả

## 🔒 Bảo mật

- ✅ **Credentials** được mã hóa và lưu an toàn
- ✅ **API keys** không được hiển thị trong code
- ✅ **Session state** để lưu trữ tạm thời
- ✅ **Error handling** không expose sensitive data

## 🐛 Troubleshooting

### Lỗi thường gặp:

1. **"Invalid property ID"**
   - Kiểm tra Property ID (phải là số)
   - Đảm bảo Service Account có quyền truy cập

2. **"OpenAI API error"**
   - Kiểm tra API key
   - Đảm bảo có credit trong tài khoản OpenAI

3. **"No data found"**
   - Kiểm tra thời gian phân tích
   - Đảm bảo có dữ liệu trong GA4

## 📈 Roadmap

- [ ] **Real-time Analytics**
- [ ] **Custom Reports**
- [ ] **Email Notifications**
- [ ] **Multi-language Support**
- [ ] **Advanced AI Features**

## 🤝 Contributing

1. **Fork** repository
2. **Create** feature branch
3. **Commit** changes
4. **Push** to branch
5. **Create** Pull Request

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

## 📞 Support

- **Email:** your-email@domain.com
- **GitHub Issues:** Tạo issue trên repository
- **Documentation:** Xem README này

---

**Made with ❤️ for E-commerce Analytics** 