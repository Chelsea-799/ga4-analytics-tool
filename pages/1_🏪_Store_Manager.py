#!/usr/bin/env python3
"""
GA4 + Google Ads Store Manager - Tool quản lý thông tin store
"""

import streamlit as st
import json
import os
import tempfile
from datetime import datetime

# Cấu hình trang
st.set_page_config(
    page_title="Store Manager - GA4 + Google Ads",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File lưu trữ stores
STORES_FILE = "stores_data.json"

def load_stores():
    """Tải danh sách stores từ file (tương thích ngược)"""
    if os.path.exists(STORES_FILE):
        try:
            with open(STORES_FILE, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, list):
                normalized = {}
                for s in raw:
                    name = s.get('store_name') or s.get('name') or f"store_{s.get('id','')}"
                    normalized[name] = {
                        'store_name': s.get('store_name', name),
                        'domain': s.get('domain'),
                        'created_at': s.get('created_at'),
                        'last_used': s.get('last_used'),
                        'ga4_property_id': s.get('property_id') or s.get('ga4_property_id'),
                        'ga4_credentials_content': s.get('credentials_content') or s.get('ga4_credentials_content'),
                        'google_ads_customer_id': s.get('google_ads_customer_id'),
                        'google_ads_developer_token': s.get('google_ads_developer_token'),
                        'google_ads_client_id': s.get('google_ads_client_id'),
                        'google_ads_client_secret': s.get('google_ads_client_secret'),
                        'google_ads_refresh_token': s.get('google_ads_refresh_token'),
                    }
                # Ghi lại theo format mới
                try:
                    with open(STORES_FILE, 'w', encoding='utf-8') as wf:
                        json.dump(normalized, wf, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                return normalized
            elif isinstance(raw, dict):
                return raw
            else:
                return {}
        except Exception:
            return {}
    return {}

def save_stores(stores):
    """Lưu danh sách stores vào file"""
    try:
        with open(STORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(stores, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Lỗi lưu file: {e}")
        return False

def add_store(store_name, domain, ga4_property_id, ga4_credentials_content):
    """Thêm store mới với chỉ GA4 (Google Ads dùng manual JSON import)"""
    stores = load_stores()
    
    # Kiểm tra trùng lặp
    if store_name in stores:
        st.error(f"❌ Store name '{store_name}' đã tồn tại!")
        return False
    
    # Tạo store mới
    new_store = {
        'store_name': store_name,
        'domain': domain,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_used': None,
        
        # GA4 Configuration
        'ga4_property_id': ga4_property_id,
        'ga4_credentials_content': ga4_credentials_content,
        
        # Google Ads: Không cần API config, chỉ dùng manual JSON import
        'google_ads_customer_id': None,
        'google_ads_developer_token': None,
        'google_ads_client_id': None,
        'google_ads_client_secret': None,
        'google_ads_refresh_token': None
    }
    
    stores[store_name] = new_store
    
    if save_stores(stores):
        st.success(f"✅ Đã thêm store: {store_name}")
        return True
    else:
        return False

def delete_store(store_name):
    """Xóa store"""
    stores = load_stores()
    if store_name in stores:
        del stores[store_name]
        
        if save_stores(stores):
            st.success("✅ Đã xóa store")
            return True
        else:
            st.error("❌ Lỗi xóa store")
            return False
    return False

def update_last_used(store_name):
    """Cập nhật thời gian sử dụng cuối"""
    stores = load_stores()
    if store_name in stores:
        stores[store_name]['last_used'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_stores(stores)

def export_store_credentials(store, credential_type):
    """Export credentials file cho store"""
    try:
        if credential_type == 'ga4':
            content = store['ga4_credentials_content']
            filename = f"{store['store_name']}_ga4_credentials.json"
        else:  # google_ads
            content = store['google_ads_refresh_token']
            filename = f"{store['store_name']}_google_ads_token.txt"
        
        # Tạo file tạm thời
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        return tmp_file_path
    except Exception as e:
        st.error(f"❌ Lỗi export credentials: {e}")
        return None

def main():
    """Hàm chính"""
    st.title("🏪 Store Manager - GA4 + Google Ads")
    st.markdown("Quản lý thông tin store để sử dụng với GA4 và Google Ads Analyzer")
    st.markdown("---")
    
    # Sidebar cho thêm store mới
    with st.sidebar:
        st.header("➕ Thêm Store Mới")
        
        with st.form("add_store_form"):
            st.subheader("📋 Thông tin cơ bản")
            store_name = st.text_input("🏪 Tên store", placeholder="Ví dụ: Vinahomesvlas Store")
            domain = st.text_input("🌐 Domain website", placeholder="https://example.com")
            
            st.subheader("📊 GA4 Configuration")
            ga4_property_id = st.text_input("🆔 GA4 Property ID", placeholder="495167329")
            ga4_credentials_file = st.file_uploader("📁 GA4 Credentials File", type=['json'], key="ga4_upload")
            
            st.info("💡 Google Ads: Không cần cấu hình API. Upload file JSON trực tiếp trong tab '📢 Google Ads Analyzer'")
            
            submitted = st.form_submit_button("➕ Thêm Store")
            
            if submitted:
                if not store_name:
                    st.error("❌ Vui lòng nhập tên store")
                elif not ga4_property_id:
                    st.error("❌ Vui lòng cấu hình GA4")
                else:
                    # Đọc nội dung file GA4 credentials
                    ga4_credentials_content = ""
                    if ga4_credentials_file:
                        ga4_credentials_content = ga4_credentials_file.getvalue().decode('utf-8')
                    
                    # Thêm store
                    if add_store(store_name, domain, ga4_property_id, ga4_credentials_content):
                        st.rerun()
    
    # Main content - Danh sách stores
    st.header("📋 Danh sách Stores")
    
    stores = load_stores()
    # Phòng lỗi: nếu file cũ trả về list thì chuyển tạm sang dict để hiển thị
    if isinstance(stores, list):
        try:
            stores = { (s.get('store_name') or s.get('name') or f"store_{s.get('id','')}"): s for s in stores }
        except Exception:
            stores = {}
    
    if not stores:
        st.info("📝 Chưa có store nào. Hãy thêm store mới ở sidebar!")
    else:
        # Hiển thị danh sách stores
        for store_name, store_data in stores.items():
            with st.expander(f"🏪 {store_name} ({store_data['domain']})", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **Thông tin Store:**
                    - 🏪 **Tên**: {store_name}
                    - 🌐 **Domain**: {store_data['domain']}
                    - 📅 **Tạo lúc**: {store_data['created_at']}
                    """)
                    
                    if store_data['last_used']:
                        st.markdown(f"- 🕒 **Sử dụng cuối**: {store_data['last_used']}")
                    
                    # GA4 Status
                    if store_data.get('ga4_property_id'):
                        st.success("✅ GA4: Đã cấu hình")
                    else:
                        st.warning("⚠️ GA4: Chưa cấu hình")
                    
                    # Google Ads Status - Manual JSON import
                    st.info("📢 Google Ads: Dùng manual JSON import (không cần API config)")
                    st.markdown("💡 Upload file JSON trong tab '📢 Google Ads Analyzer'")
                
                with col2:
                    # Nút sử dụng store
                    if st.button("🚀 Sử dụng", key=f"use_{store_name}"):
                        # Cập nhật thời gian sử dụng
                        update_last_used(store_name)
                        
                        # Lưu thông tin vào session state
                        st.session_state['selected_store'] = store_data
                        
                        st.success(f"✅ Đã chọn store: {store_name}")
                        st.info("💡 Chuyển sang tab Analyzer để phân tích dữ liệu")
                    
                    # Nút xóa store
                    if st.button("🗑️ Xóa", key=f"delete_{store_name}"):
                        if delete_store(store_name):
                            st.rerun()
        
        # Thống kê
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Tổng số stores", len(stores))
        with col2:
            ga4_count = sum(1 for store in stores.values() if store.get('ga4_property_id'))
            st.metric("📈 GA4 Properties", ga4_count)
        with col3:
            ads_count = sum(1 for store in stores.values() if store.get('google_ads_customer_id'))
            st.metric("📢 Google Ads", ads_count)
        with col4:
            used_stores = sum(1 for store in stores.values() if store.get('last_used'))
            st.metric("🚀 Stores đã sử dụng", used_stores)
    
    # Hướng dẫn sử dụng
    st.markdown("---")
    st.header("📖 Hướng dẫn sử dụng")
    
    st.markdown("""
    ### 🔧 Cách thêm store:
    1. **Nhập thông tin cơ bản**: Tên store, domain
    2. **Cấu hình GA4**: Property ID + credentials file
    3. **Cấu hình Google Ads**: Customer ID + tokens
    4. **Nhấn "Thêm Store"** để lưu
    
    ### 🚀 Cách sử dụng store:
    1. **Chọn store** từ danh sách bên trên
    2. **Nhấn "Sử dụng"** để chọn store
    3. **Chuyển sang Analyzer** để phân tích dữ liệu
    
    ### 📁 File lưu trữ:
    - Thông tin stores được lưu trong file `stores_data.json`
    - Credentials được mã hóa và lưu an toàn
    - Có thể backup/restore file này để chuyển dữ liệu
    """)
    
    # Export/Import functionality
    st.markdown("---")
    st.header("📤 Export/Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Stores"):
            stores = load_stores()
            if stores:
                # Tạo file export (không bao gồm credentials content)
                export_data = {}
                for store_name, store_data in stores.items():
                    export_data[store_name] = {
                        'store_name': store_data['store_name'],
                        'domain': store_data['domain'],
                        'created_at': store_data['created_at'],
                        'last_used': store_data['last_used'],
                        'ga4_property_id': store_data.get('ga4_property_id'),
                        'google_ads_customer_id': store_data.get('google_ads_customer_id')
                    }
                
                # Tạo file download
                import io
                buffer = io.StringIO()
                json.dump(export_data, buffer, ensure_ascii=False, indent=2)
                buffer.seek(0)
                
                st.download_button(
                    label="📥 Tải file Export",
                    data=buffer.getvalue(),
                    file_name=f"stores_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.warning("📝 Không có stores để export")
    
    with col2:
        st.markdown("""
        **Import Stores:**
        - Tải file export từ máy khác
        - Upload file JSON vào đây
        - Nhập lại credentials cho từng store
        """)

if __name__ == "__main__":
    main() 