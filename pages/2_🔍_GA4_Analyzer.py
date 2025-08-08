#!/usr/bin/env python3
"""
GA4 Analyzer UI - Giao diện web cho tool phân tích GA4
"""

import streamlit as st
import json
import os
import pandas as pd
from openai import OpenAI
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Metric,
    Dimension,
    RunReportRequest
)
from google.oauth2 import service_account
import tempfile

# Cấu hình OpenAI API key (người dùng phải nhập)
DEFAULT_OPENAI_API_KEY = ""

# Cấu hình trang
st.set_page_config(
    page_title="GA4 Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_ga4_client(credentials_file):
    """Tạo GA4 client từ credentials file"""
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_file)
        client = BetaAnalyticsDataClient(credentials=credentials)
        return client
    except Exception as e:
        st.error(f"❌ Lỗi tạo GA4 client: {e}")
        return None

def fetch_basic_metrics(client, property_id, days=30):
    """Lấy các chỉ số cơ bản từ GA4"""
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="totalUsers"),
                Metric(name="sessions"),
                Metric(name="screenPageViews"),
                Metric(name="transactions"),
                Metric(name="totalRevenue")
            ],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")]
        )

        response = client.run_report(request)
        
        rows = []
        for row in response.rows:
            record = {
                "date": row.dimension_values[0].value,
                "totalUsers": int(row.metric_values[0].value),
                "sessions": int(row.metric_values[1].value),
                "screenPageViews": int(row.metric_values[2].value),
                "transactions": int(row.metric_values[3].value),
                "totalRevenue": float(row.metric_values[4].value)
            }
            rows.append(record)

        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ Lỗi lấy dữ liệu cơ bản: {e}")
        return pd.DataFrame()

def test_openai_api(api_key=None):
    """Test OpenAI API key"""
    if not api_key:
        api_key = st.session_state.get('openai_api_key', DEFAULT_OPENAI_API_KEY)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",  # Sử dụng GPT-4o (OpenAI 4.0)
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        return True
    except Exception as e:
        st.error(f"❌ OpenAI API key không hợp lệ: {e}")
        return False

def fetch_product_views(client, property_id, days=30):
    """Lấy dữ liệu view sản phẩm từ GA4 - dựa trên page title"""
    try:
        # Request lấy dữ liệu view theo page title
        views_request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                Dimension(name="pageTitle")
            ],
            metrics=[
                Metric(name="screenPageViews")
            ],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")]
        )

        views_response = client.run_report(views_request)
        
        # Xử lý dữ liệu view
        views_data = {}
        for row in views_response.rows:
            page_title = row.dimension_values[0].value
            page_views = int(row.metric_values[0].value)
            
            # Hiển thị tất cả các trang có dữ liệu view
            if (page_title and 
                page_title not in ['(not set)', '(not provided)']):
                
                # Sử dụng page title làm tên sản phẩm
                product_name = page_title
                
                if product_name not in views_data:
                    views_data[product_name] = {
                        'views': page_views,
                        'pageViews': page_views
                    }
                else:
                    views_data[product_name]['views'] += page_views
                    views_data[product_name]['pageViews'] += page_views
        
        # Chuyển thành DataFrame
        if views_data:
            views_list = []
            for product_name, data in views_data.items():
                views_list.append({
                    'itemName': product_name,
                    'views': data['views'],
                    'pageViews': data['pageViews']
                })
            
            df = pd.DataFrame(views_list)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Lỗi lấy dữ liệu view sản phẩm: {e}")
        return pd.DataFrame()

# Hàm create_summary_charts đã được xóa vì không cần thiết

def fetch_product_performance(client, property_id, days=30):
    """Lấy dữ liệu sản phẩm từ GA4"""
    try:
        # Request 1: Lấy events theo eventName
        events_request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="eventCount")],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")]
        )

        events_response = client.run_report(events_request)
        
        # Xử lý dữ liệu events
        events_data = {}
        for row in events_response.rows:
            event_name = row.dimension_values[0].value
            event_count = int(row.metric_values[0].value)
            if event_name in ['purchase', 'add_to_cart', 'begin_checkout']:
                events_data[event_name] = event_count
        
        # Request 2: Lấy dữ liệu sản phẩm với revenue
        products_request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="itemName")],
            metrics=[
                Metric(name="itemRevenue"),
                Metric(name="itemPurchaseQuantity")
            ],
            date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")]
        )

        products_response = client.run_report(products_request)
        
        # Xử lý dữ liệu sản phẩm
        products_data = []
        for row in products_response.rows:
            item_name = row.dimension_values[0].value
            revenue = float(row.metric_values[0].value)
            quantity = int(row.metric_values[1].value) if row.metric_values[1].value else 0
            
            # Bỏ điều kiện revenue > 0 để hiển thị tất cả sản phẩm có view
            if item_name:
                products_data.append({
                    'itemName': item_name,
                    'itemRevenue': revenue,
                    'itemPurchaseQuantity': quantity,
                    'transactions': quantity,  # Số lượng = số giao dịch
                    'addToCarts': events_data.get('add_to_cart', 0),  # Ước tính từ tổng
                    'beginCheckouts': events_data.get('begin_checkout', 0),  # Ước tính từ tổng
                    'ecommercePurchases': events_data.get('purchase', 0),  # Ước tính từ tổng
                    'eventCount': events_data.get('purchase', 0),  # Tổng events
                    'itemCategory': 'General'
                })
        
        # Kết hợp với dữ liệu view từ page title
        views_df = fetch_product_views(client, property_id, days)
        
        if products_data:
            df = pd.DataFrame(products_data)
            
            # Nếu có dữ liệu view, merge vào
            if not views_df.empty:
                # Merge dữ liệu view vào products
                df = df.merge(views_df, on='itemName', how='outer')
                # Fill NaN values
                df['views'] = df['views'].fillna(0)
                df['pageViews'] = df['pageViews'].fillna(0)
                df['itemRevenue'] = df['itemRevenue'].fillna(0)
                df['transactions'] = df['transactions'].fillna(0)
                df['itemPurchaseQuantity'] = df['itemPurchaseQuantity'].fillna(0)
                df['eventCount'] = df['eventCount'].fillna(0)
                df['ecommercePurchases'] = df['ecommercePurchases'].fillna(0)
                df['addToCarts'] = df['addToCarts'].fillna(0)
                df['beginCheckouts'] = df['beginCheckouts'].fillna(0)
                df['itemCategory'] = df['itemCategory'].fillna('General')
            
            return df
        elif not views_df.empty:
            # Nếu không có products nhưng có views, sử dụng views data
            st.info("💡 Hiển thị dữ liệu từ page views (chưa có giao dịch)")
            views_df['itemRevenue'] = 0
            views_df['transactions'] = 0
            views_df['itemPurchaseQuantity'] = 0
            views_df['eventCount'] = 0
            views_df['ecommercePurchases'] = 0
            views_df['addToCarts'] = 0
            views_df['beginCheckouts'] = 0
            views_df['itemCategory'] = 'Page Views'
            return views_df
        else:
            st.warning("⚠️ Không tìm thấy dữ liệu sản phẩm")
            # Trả về DataFrame rỗng với giá trị 0
            empty_df = pd.DataFrame({
                'itemName': ['No Products'],
                'itemRevenue': [0.0],
                'transactions': [0],
                'itemPurchaseQuantity': [0],
                'eventCount': [0],
                'ecommercePurchases': [0],
                'addToCarts': [0],
                'beginCheckouts': [0],
                'itemCategory': ['No Category']
            })
            return empty_df
        
    except Exception as e:
        st.error(f"❌ Lỗi lấy dữ liệu sản phẩm: {e}")
        # Trả về DataFrame với giá trị 0
        error_df = pd.DataFrame({
            'itemName': ['Error - No Data'],
            'itemRevenue': [0.0],
            'transactions': [0],
            'itemPurchaseQuantity': [0],
            'eventCount': [0],
            'ecommercePurchases': [0],
            'addToCarts': [0],
            'beginCheckouts': [0],
            'itemCategory': ['Error']
        })
        return error_df

def main():
    """Hàm chính"""
    st.title("🔍 GA4 Analyzer - Tool phân tích GA4")
    st.markdown("---")
    
    # Sidebar cho cấu hình
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        
        # Cấu hình OpenAI API key
        st.subheader("🤖 OpenAI API Key (GPT-4o)")
        st.info("🚀 Tool đã được cấu hình để sử dụng GPT-4o (OpenAI 4.0)")
        st.warning("⚠️ API key là bắt buộc để sử dụng phân tích AI")
        
        # Lấy API key từ session state hoặc sử dụng default
        openai_key = st.session_state.get('openai_api_key', DEFAULT_OPENAI_API_KEY)
        
        # Input cho API key
        new_api_key = st.text_input(
            "🔑 OpenAI API Key (Bắt buộc)", 
            value=openai_key,
            type="password",
            help="Nhập OpenAI API key để sử dụng phân tích AI"
        )
        
        # Kiểm tra API key
        if not new_api_key or new_api_key.strip() == "":
            st.error("❌ Vui lòng nhập OpenAI API key để sử dụng phân tích AI")
            st.warning("💡 API key là bắt buộc để sử dụng tính năng phân tích AI")
        else:
            st.success("✅ API key đã được nhập")
        
        # Hướng dẫn lấy API key
        with st.expander("📖 Hướng dẫn lấy OpenAI API Key"):
            st.markdown("""
            1. **Truy cập:** https://platform.openai.com/account/api-keys
            2. **Đăng nhập** vào tài khoản OpenAI
            3. **Tạo API key mới** hoặc copy key có sẵn
            4. **Paste vào ô bên trên**
            5. **Test API key** bằng nút bên dưới
            
            **💡 Tool đã được cấu hình để sử dụng GPT-4o (OpenAI 4.0)**
            """)
        
        # Cập nhật API key nếu thay đổi
        if new_api_key != openai_key:
            st.session_state['openai_api_key'] = new_api_key
            st.success("✅ API key đã được cập nhật!")
        
        # Test API key
        if st.button("🔑 Test OpenAI API"):
            with st.spinner("🔄 Đang test API key..."):
                if test_openai_api(new_api_key):
                    st.success("✅ OpenAI API key hoạt động tốt!")
                else:
                    st.error("❌ OpenAI API key có vấn đề!")
        
        st.markdown("---")
        
        # Chọn phương thức nhập credentials
        st.subheader("📁 Credentials")
        
        # Kiểm tra xem có store đã được chọn từ Store Manager không
        selected_store = st.session_state.get('selected_store', None)
        
        if selected_store:
            ga4_property_id_selected = selected_store.get('ga4_property_id') or selected_store.get('property_id') or ""
            st.success(f"✅ Store đã chọn: {selected_store.get('store_name', 'N/A')}")
            st.info(f"🌐 Domain: {selected_store.get('domain', 'N/A')}")
            st.info(f"🆔 Property ID: {ga4_property_id_selected}")
            
            if st.button("🔄 Chọn store khác"):
                del st.session_state['selected_store']
                st.rerun()
            
            # Tạo file credentials tạm nếu có nội dung credentials trong store
            credentials_path = None
            ga4_credentials_content = selected_store.get('ga4_credentials_content') or selected_store.get('credentials_content')
            if ga4_credentials_content:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as tmp_file:
                        tmp_file.write(ga4_credentials_content)
                        credentials_path = tmp_file.name
                except Exception:
                    credentials_path = None
            else:
                credentials_path = selected_store.get('credentials_path')
        else:
            st.info("💡 Chưa có store nào được chọn")
            st.markdown("**Chọn phương thức:**")
            
            # Option 1: Upload file
            if st.checkbox("📁 Upload file credentials.json"):
                uploaded_file = st.file_uploader("Chọn file credentials.json", type=['json'], key="upload_analyzer")
                
                if uploaded_file is not None:
                    # Lưu file tạm thời
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        credentials_path = tmp_file.name
                    st.success("✅ File credentials đã được upload")
                    st.info(f"📁 File: {credentials_path}")
                else:
                    credentials_path = None
            else:
                credentials_path = None
            
            # Option 2: Chuyển sang Store Manager
            st.markdown("---")
            st.markdown("**Hoặc:**")
            if st.button("🏪 Mở Store Manager"):
                st.switch_page("pages/1_🏪_Store_Manager.py")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📋 Thông tin Store")
        
        # Form nhập thông tin
        with st.form("store_info"):
            # Tự động điền thông tin từ store đã chọn
            default_store_name = selected_store.get('store_name', "") if selected_store else ""
            default_domain = selected_store.get('domain', "") if selected_store else ""
            default_property_id = (
                (selected_store.get('ga4_property_id') or selected_store.get('property_id')) if selected_store else ""
            )
            
            store_name = st.text_input("🏪 Tên store", value=default_store_name, placeholder="Ví dụ: Vinahomesvlas Store")
            domain = st.text_input("🌐 Domain website", value=default_domain, placeholder="https://example.com")
            property_id = st.text_input("🆔 GA4 Property ID", value=default_property_id, placeholder="495167329")
            days = st.number_input("📅 Số ngày phân tích", min_value=1, max_value=365, value=30)
            
            submitted = st.form_submit_button("🚀 Phân tích dữ liệu")
    
    with col2:
        st.header("📊 Hướng dẫn")
        st.markdown("""
        1. **Upload file credentials.json** từ Google Analytics
        2. **Nhập thông tin store** bên trái
        3. **Nhấn "Phân tích dữ liệu"**
        4. **Xem kết quả** bên dưới
        5. **Phân tích AI** sẽ tự động chạy
        """)
        
        st.info("🤖 Phân tích AI đã được cấu hình sẵn")
    
    # Xử lý khi submit form
    if submitted:
        if not all([store_name, domain, property_id, credentials_path]):
            st.error("❌ Vui lòng điền đầy đủ thông tin và upload file credentials")
            return
        
        # Hiển thị thông tin store
        st.markdown("---")
        st.header(f"📊 Phân tích GA4 - {store_name.upper()}")
        
        # Kiểm tra file credentials
        if not os.path.exists(credentials_path):
            st.error(f"❌ File credentials không tồn tại: {credentials_path}")
            return
        
        # Tạo client
        with st.spinner("🔄 Đang kết nối GA4..."):
            client = get_ga4_client(credentials_path)
            if not client:
                return
        
        st.success("✅ Kết nối GA4 thành công!")
        
        # Lấy dữ liệu
        with st.spinner("📈 Đang lấy dữ liệu..."):
            df = fetch_product_performance(client, property_id, days)
            basic_df = fetch_basic_metrics(client, property_id, days)
            views_df = fetch_product_views(client, property_id, days)
        
        # Hiển thị chỉ số cơ bản
        if not basic_df.empty:
            total_users = basic_df['totalUsers'].sum()
            total_sessions = basic_df['sessions'].sum()
            total_views = basic_df['screenPageViews'].sum()
            total_transactions = basic_df['transactions'].sum()
            total_revenue = basic_df['totalRevenue'].sum()
            
            # Tính toán metrics bổ sung
            conversion_rate = (total_transactions / total_sessions * 100) if total_sessions > 0 else 0
            avg_order_value = (total_revenue / total_transactions) if total_transactions > 0 else 0
            
            # Hiển thị metrics trong columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("👥 Users", f"{total_users:,}")
                st.metric("🔄 Sessions", f"{total_sessions:,}")
            
            with col2:
                st.metric("👀 Page Views", f"{total_views:,}")
                st.metric("🛒 Transactions", f"{total_transactions:,}")
            
            with col3:
                st.metric("💰 Revenue", f"${total_revenue:,.2f}")
                st.metric("📊 Conversion Rate", f"{conversion_rate:.2f}%")
            
            with col4:
                st.metric("💵 Avg Order Value", f"${avg_order_value:.2f}")
                st.metric("📅 Thời gian", f"{days} ngày")
        else:
            st.warning("❌ Không có dữ liệu cơ bản")
        
        # Hiển thị dữ liệu sản phẩm
        if not df.empty and len(df) > 0 and df['itemName'].iloc[0] not in ['No Products', 'Error - No Data']:
            st.markdown("---")
            st.header("📦 Dữ liệu sản phẩm")
            
            # Thống kê tổng quan
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Số sản phẩm", len(df))
            with col2:
                st.metric("Tổng doanh thu", f"${df['itemRevenue'].sum():,.2f}")
            with col3:
                st.metric("Tổng giao dịch", f"{df['transactions'].sum():,}")
            with col4:
                st.metric("Tổng events", f"{df['eventCount'].sum():,}")
            
            # Thêm thống kê views nếu có
            if 'views' in df.columns:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tổng views", f"{df['views'].sum():,}")
                with col2:
                    st.metric("Tổng page views", f"{df['pageViews'].sum():,}")
                with col3:
                    st.metric("Sản phẩm có view", len(df[df['views'] > 0]))
                with col4:
                    st.metric("Sản phẩm có giao dịch", len(df[df['transactions'] > 0]))
            
            # Bảng chi tiết sản phẩm
            st.subheader("📋 Chi tiết sản phẩm")
            display_columns = ['itemName', 'itemRevenue', 'transactions', 'itemPurchaseQuantity']
            if 'views' in df.columns:
                display_columns.extend(['views', 'pageViews'])
            display_columns.extend(['addToCarts', 'beginCheckouts', 'ecommercePurchases'])
            
            display_df = df[display_columns].copy()
            
            # Tạo tên cột tương ứng với số cột thực tế
            column_names = ['Tên sản phẩm', 'Doanh thu', 'Giao dịch', 'Số lượng']
            if 'views' in df.columns:
                column_names.extend(['Views', 'Page Views'])
            column_names.extend(['Thêm giỏ hàng', 'Bắt đầu checkout', 'Mua hàng'])
            
            # Kiểm tra số lượng cột
            if len(display_df.columns) == len(column_names):
                display_df.columns = column_names
                display_df['Doanh thu'] = display_df['Doanh thu'].round(2)
                st.dataframe(display_df, use_container_width=True)
            else:
                st.error(f"❌ Lỗi: Số cột không khớp. Có {len(display_df.columns)} cột nhưng chỉ có {len(column_names)} tên")
                st.write("Các cột hiện có:", list(display_df.columns))
                st.write("Tên cột mong muốn:", column_names)
                # Hiển thị DataFrame gốc nếu có lỗi
                st.dataframe(display_df, use_container_width=True)
            
            # Bảng sơ đồ thống kê tổng hợp - Kết hợp cả 3 loại
            st.subheader("📊 Bảng sơ đồ thống kê tổng hợp - So sánh 3 tiêu chí")
            
            # Tạo DataFrame tổng hợp thông minh
            combined_data = []
            
            # Lấy top 10 từ mỗi loại
            top_revenue = df.nlargest(10, 'itemRevenue')
            top_sales = df.nlargest(10, 'transactions')
            top_views = df.nlargest(10, 'views') if 'views' in df.columns else pd.DataFrame()
            
            # Tạo set tất cả sản phẩm unique
            all_products = set()
            all_products.update(top_revenue['itemName'].tolist())
            all_products.update(top_sales['itemName'].tolist())
            if not top_views.empty:
                all_products.update(top_views['itemName'].tolist())
            
            # Tạo dữ liệu tổng hợp cho từng sản phẩm
            for product in all_products:
                # Tìm thông tin sản phẩm trong từng DataFrame
                revenue_info = df[df['itemName'] == product].iloc[0] if not df[df['itemName'] == product].empty else None
                revenue_rank = top_revenue[top_revenue['itemName'] == product].index.tolist()
                sales_rank = top_sales[top_sales['itemName'] == product].index.tolist()
                views_rank = top_views[top_views['itemName'] == product].index.tolist() if not top_views.empty else []
                
                if revenue_info is not None:
                    # Xác định loại sản phẩm
                    categories = []
                    if revenue_rank:
                        categories.append('🏆 Doanh thu')
                    if sales_rank:
                        categories.append('🛒 Bán chạy')
                    if views_rank:
                        categories.append('👁️ Nhiều view')
                    
                    category_text = ' | '.join(categories) if categories else '📊 Khác'
                    
                    combined_data.append({
                        'Tên sản phẩm': product,
                        'Doanh thu ($)': revenue_info['itemRevenue'],
                        'Giao dịch': revenue_info['transactions'],
                        'Views': revenue_info.get('views', 0),
                        'Hạng doanh thu': revenue_rank[0] + 1 if revenue_rank else '-',
                        'Hạng bán chạy': sales_rank[0] + 1 if sales_rank else '-',
                        'Hạng views': views_rank[0] + 1 if views_rank else '-',
                        'Loại': category_text,
                        'Tổng điểm': (
                            (11 - (revenue_rank[0] + 1) if revenue_rank else 0) +
                            (11 - (sales_rank[0] + 1) if sales_rank else 0) +
                            (11 - (views_rank[0] + 1) if views_rank else 0)
                        )
                    })
            
            # Tạo DataFrame và sắp xếp theo tổng điểm
            combined_df = pd.DataFrame(combined_data)
            combined_df = combined_df.sort_values('Tổng điểm', ascending=False)
            
            # Format dữ liệu hiển thị
            display_df = combined_df.copy()
            display_df['Doanh thu ($)'] = display_df['Doanh thu ($)'].apply(lambda x: f"${x:,.2f}")
            display_df['Tổng điểm'] = display_df['Tổng điểm'].astype(int)
            
            # Hiển thị bảng tổng hợp
            st.dataframe(display_df, use_container_width=True)
            
            # Thống kê phân loại
            st.subheader("📈 Thống kê phân loại sản phẩm")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                revenue_only = len(combined_df[combined_df['Loại'] == '🏆 Doanh thu'])
                st.metric("🏆 Chỉ doanh thu", revenue_only)
            
            with col2:
                sales_only = len(combined_df[combined_df['Loại'] == '🛒 Bán chạy'])
                st.metric("🛒 Chỉ bán chạy", sales_only)
            
            with col3:
                views_only = len(combined_df[combined_df['Loại'] == '👁️ Nhiều view'])
                st.metric("👁️ Chỉ nhiều view", views_only)
            
            # Sản phẩm xuất hiện trong nhiều danh sách
            multi_category = combined_df[combined_df['Loại'].str.contains('\|')]
            if not multi_category.empty:
                st.success(f"🎯 Sản phẩm xuất hiện trong nhiều danh sách: {len(multi_category)}")
                for _, row in multi_category.head(5).iterrows():
                    st.write(f"  • {row['Tên sản phẩm']} - {row['Loại']}")
            
            # Top 5 sản phẩm toàn diện nhất
            st.subheader("🏆 Top 5 sản phẩm toàn diện nhất")
            top_comprehensive = combined_df.head(5)
            for i, (_, row) in enumerate(top_comprehensive.iterrows(), 1):
                st.write(f"{i}. **{row['Tên sản phẩm']}** - Điểm: {row['Tổng điểm']}")
                st.write(f"   Doanh thu: {row['Doanh thu ($)']} | Giao dịch: {row['Giao dịch']} | Views: {row['Views']}")
                st.write(f"   Loại: {row['Loại']}")
                st.write("---")
            
            # Bỏ qua phần biểu đồ - chỉ giữ lại bảng tổng hợp
            
            # Thống kê tổng quan
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏆 Top doanh thu cao nhất", f"${top_revenue['itemRevenue'].iloc[0]:,.2f}")
            with col2:
                st.metric("🛒 Top bán chạy nhất", f"{top_sales['transactions'].iloc[0]:,} giao dịch")
            with col3:
                if 'views' in df.columns:
                    st.metric("👁️ Top view nhiều nhất", f"{top_views['views'].iloc[0]:,} views")
                else:
                    st.metric("👁️ Top view nhiều nhất", "N/A")
            
            # Phân tích tương quan
            st.subheader("📈 Phân tích tương quan")
            
            # Tìm sản phẩm xuất hiện trong cả 3 danh sách
            top_revenue_names = set(top_revenue['itemName'].tolist())
            top_sales_names = set(top_sales['itemName'].tolist())
            top_views_names = set(top_views['itemName'].tolist()) if 'views' in df.columns else set()
            
            # Sản phẩm xuất hiện trong cả 3 danh sách
            all_three = top_revenue_names & top_sales_names & top_views_names
            revenue_and_sales = (top_revenue_names & top_sales_names) - all_three
            revenue_and_views = (top_revenue_names & top_views_names) - all_three
            sales_and_views = (top_sales_names & top_views_names) - all_three
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎯 Sản phẩm xuất hiện trong nhiều danh sách:**")
                if all_three:
                    st.success(f"✅ Cả 3 danh sách: {len(all_three)} sản phẩm")
                    for product in list(all_three)[:5]:  # Hiển thị tối đa 5 sản phẩm
                        st.write(f"  • {product}")
                if revenue_and_sales:
                    st.info(f"💡 Doanh thu + Bán chạy: {len(revenue_and_sales)} sản phẩm")
                if revenue_and_views:
                    st.info(f"💡 Doanh thu + Nhiều view: {len(revenue_and_views)} sản phẩm")
                if sales_and_views:
                    st.info(f"💡 Bán chạy + Nhiều view: {len(sales_and_views)} sản phẩm")
            
            with col2:
                st.markdown("**📊 Thống kê phân loại:**")
                st.write(f"🏆 Top doanh thu: {len(top_revenue_names)} sản phẩm")
                st.write(f"🛒 Top bán chạy: {len(top_sales_names)} sản phẩm")
                if 'views' in df.columns:
                    st.write(f"👁️ Top view: {len(top_views_names)} sản phẩm")
                
                # Tính tỷ lệ overlap
                if 'views' in df.columns:
                    overlap_rate = len(all_three) / min(len(top_revenue_names), len(top_sales_names), len(top_views_names)) * 100
                    st.metric("📊 Tỷ lệ overlap", f"{overlap_rate:.1f}%")
            
            # Top sản phẩm chi tiết (giữ lại để tham khảo)
            with st.expander("📋 Xem chi tiết từng danh sách"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🏆 Top 10 Doanh thu:**")
                    for i, (_, row) in enumerate(top_revenue.iterrows(), 1):
                        st.write(f"{i}. {row['itemName']}: ${row['itemRevenue']:,.2f}")
                
                with col2:
                    st.markdown("**🛒 Top 10 Bán chạy:**")
                    for i, (_, row) in enumerate(top_sales.iterrows(), 1):
                        st.write(f"{i}. {row['itemName']}: {row['transactions']:,} giao dịch")
                
                with col3:
                    if 'views' in df.columns:
                        st.markdown("**👁️ Top 10 Views:**")
                        for i, (_, row) in enumerate(top_views.iterrows(), 1):
                            st.write(f"{i}. {row['itemName']}: {row['views']:,} views")
                    else:
                        st.markdown("**👁️ Top 10 Views:**")
                        st.write("Không có dữ liệu views")
            
            # Hiển thị top trang có nhiều view nhất (từ views_df riêng biệt)
            if not views_df.empty and 'views' not in df.columns:
                st.subheader("👁️ Top 10 trang có nhiều view nhất")
                top_views = views_df.nlargest(10, 'views')
                for i, (_, row) in enumerate(top_views.iterrows(), 1):
                    st.write(f"{i}. **{row['itemName']}**: {row['views']:,} views")
                
                # Bảng chi tiết view trang
                st.subheader("📋 Chi tiết view trang")
                display_views_df = views_df[['itemName', 'views', 'pageViews']].copy()
                display_views_df.columns = ['Tên trang', 'Views', 'Page Views']
                st.dataframe(display_views_df, use_container_width=True)
                
                # Thống kê view tổng quan
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tổng views", f"{views_df['views'].sum():,}")
                with col2:
                    st.metric("Tổng page views", f"{views_df['pageViews'].sum():,}")
                with col3:
                    st.metric("Số trang có view", len(views_df[views_df['views'] > 0]))
            elif 'views' not in df.columns:
                st.subheader("👁️ Top trang có nhiều view nhất")
                st.info("💡 Chưa có dữ liệu view trang")
            
            # Phân tích AI tự động
            st.markdown("---")
            st.subheader("🤖 Phân tích AI")
            
            # Kiểm tra API key trước khi phân tích
            current_api_key = st.session_state.get('openai_api_key', "")
            if not current_api_key or current_api_key.strip() == "":
                st.error("❌ Vui lòng nhập OpenAI API key trong sidebar để sử dụng phân tích AI")
                st.info("💡 Nhập API key và test trước khi phân tích")
                return
            
            with st.spinner("🧠 Đang phân tích AI..."):
                try:
                    # Chuẩn bị dữ liệu cho AI
                    total_revenue = df['itemRevenue'].sum()
                    total_transactions = df['transactions'].sum()
                    
                    # Tạo bảng dữ liệu sản phẩm (chỉ top 20 để giảm tokens)
                    products_data = []
                    top_products = df.nlargest(20, 'itemRevenue')  # Chỉ lấy top 20
                    
                    for _, row in top_products.iterrows():
                        # Tìm thông tin view cho sản phẩm này (so sánh tên sản phẩm)
                        view_info = views_df[views_df['itemName'].str.contains(row['itemName'], case=False, na=False)]
                        if view_info.empty:
                            # Nếu không tìm thấy, tìm sản phẩm có tên tương tự
                            view_info = views_df[views_df['itemName'].str.contains(row['itemName'].split()[0], case=False, na=False)]
                        
                        views = view_info['views'].iloc[0] if not view_info.empty else 0
                        page_views = view_info['pageViews'].iloc[0] if not view_info.empty else 0
                        
                        # Rút gọn tên sản phẩm để giảm tokens
                        product_name = row['itemName']
                        if len(product_name) > 50:
                            product_name = product_name[:47] + "..."
                        
                        products_data.append({
                            'Tên sản phẩm': product_name,
                            'Doanh thu': f"${row['itemRevenue']:,.2f}",
                            'Giao dịch': int(row['transactions']),
                            'Views': int(views)
                        })
                    
                    # Tạo prompt cho AI
                    total_views = views_df['views'].sum() if not views_df.empty else 0
                    total_page_views = views_df['pageViews'].sum() if not views_df.empty else 0
                    
                    prompt = f"""Phân tích dữ liệu e-commerce cho store "{store_name}" ({domain}) trong {days} ngày:

📊 TỔNG QUAN: Doanh thu ${total_revenue:,.2f}, {total_transactions:,} giao dịch, {total_views:,} views
📋 TOP 20 SẢN PHẨM: {json.dumps(products_data, ensure_ascii=False)}

Phân tích:
1. 🏆 Sản phẩm thế mạnh (doanh thu + views cao)
2. 🌟 Sản phẩm tiềm năng (nhiều views, ít doanh thu)  
3. ⚠️ Sản phẩm cần cải thiện
4. 📈 Khuyến nghị marketing và tối ưu

Trả lời bằng tiếng Việt, ngắn gọn."""
                    
                    # Gọi OpenAI API - Sử dụng API key đã kiểm tra
                    from openai import OpenAI
                    client = OpenAI(api_key=current_api_key)
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",  # Sử dụng GPT-4o (OpenAI 4.0)
                        messages=[
                            {"role": "system", "content": f"Bạn là chuyên gia phân tích dữ liệu e-commerce với kinh nghiệm sâu về Google Analytics 4 và tối ưu hóa doanh thu cho store {store_name}."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    ai_analysis = response.choices[0].message.content.strip()
                    st.markdown(ai_analysis)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi phân tích AI: {e}")
                    st.info("💡 Có thể do:")
                    st.write("- API key OpenAI không đúng hoặc hết hạn")
                    st.write("- Kết nối internet không ổn định")
                    st.write("- OpenAI service tạm thời không khả dụng")
                    st.write("**Hãy kiểm tra API key và thử lại!**")
        else:
            st.markdown("---")
            st.header("📦 Dữ liệu sản phẩm")
            st.warning("❌ Không có dữ liệu sản phẩm")
            st.info("💡 Có thể do:")
            st.write("- Chưa có giao dịch trong thời gian này")
            st.write("- Tracking ecommerce chưa được thiết lập")
            st.write("- Property ID không đúng")
        
        # Xóa file tạm (chỉ xóa nếu là file tạm thời)
        if credentials_path and os.path.exists(credentials_path) and 'tmp' in credentials_path:
            try:
                os.unlink(credentials_path)
            except:
                pass

if __name__ == "__main__":
    main() 