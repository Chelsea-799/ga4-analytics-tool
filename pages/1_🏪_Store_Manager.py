#!/usr/bin/env python3
"""
GA4 Store Manager - Tool quản lý thông tin store
"""

import streamlit as st
import json
import os
import tempfile
from datetime import datetime
import pandas as pd

# Cấu hình trang
st.set_page_config(
    page_title="GA4 Store Manager",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File lưu trữ stores
STORES_FILE = "stores_data.json"

def load_stores():
    """Tải danh sách stores từ file"""
    if os.path.exists(STORES_FILE):
        try:
            with open(STORES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_stores(stores):
    """Lưu danh sách stores vào file"""
    try:
        with open(STORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(stores, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Lỗi lưu file: {e}")
        return False

def add_store(store_name, domain, property_id, credentials_content):
    """Thêm store mới"""
    stores = load_stores()
    
    # Kiểm tra trùng lặp
    for store in stores:
        if store['property_id'] == property_id:
            st.error(f"❌ Property ID {property_id} đã tồn tại!")
            return False
    
    # Tạo store mới
    new_store = {
        'id': len(stores) + 1,
        'store_name': store_name,
        'domain': domain,
        'property_id': property_id,
        'credentials_content': credentials_content,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_used': None
    }
    
    stores.append(new_store)
    
    if save_stores(stores):
        st.success(f"✅ Đã thêm store: {store_name}")
        return True
    else:
        st.error("❌ Lỗi lưu store")
        return False

def delete_store(store_id):
    """Xóa store"""
    stores = load_stores()
    stores = [store for store in stores if store['id'] != store_id]
    
    if save_stores(stores):
        st.success("✅ Đã xóa store")
        return True
    else:
        st.error("❌ Lỗi xóa store")
        return False

def update_last_used(store_id):
    """Cập nhật thời gian sử dụng cuối"""
    stores = load_stores()
    for store in stores:
        if store['id'] == store_id:
            store['last_used'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    
    save_stores(stores)

def export_store_credentials(store):
    """Export credentials file cho store"""
    try:
        # Tạo file tạm thời
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as tmp_file:
            tmp_file.write(store['credentials_content'])
            tmp_file_path = tmp_file.name
        
        return tmp_file_path
    except Exception as e:
        st.error(f"❌ Lỗi export credentials: {e}")
        return None

def main():
    """Hàm chính"""
    st.title("🏪 GA4 Store Manager")
    st.markdown("Quản lý thông tin store để sử dụng với GA4 Analyzer")
    st.markdown("---")
    
    # Sidebar cho thêm store mới
    with st.sidebar:
        st.header("➕ Thêm Store Mới")
        
        with st.form("add_store_form"):
            store_name = st.text_input("🏪 Tên store", placeholder="Ví dụ: Vinahomesvlas Store")
            domain = st.text_input("🌐 Domain website", placeholder="https://example.com")
            property_id = st.text_input("🆔 GA4 Property ID", placeholder="495167329")
            
            st.markdown("📁 Upload Credentials File")
            uploaded_file = st.file_uploader("Chọn file credentials.json", type=['json'], key="upload_new")
            
            submitted = st.form_submit_button("➕ Thêm Store")
            
            if submitted:
                if not all([store_name, domain, property_id, uploaded_file]):
                    st.error("❌ Vui lòng điền đầy đủ thông tin và upload file credentials")
                else:
                    # Đọc nội dung file credentials
                    credentials_content = uploaded_file.getvalue().decode('utf-8')
                    
                    # Thêm store
                    if add_store(store_name, domain, property_id, credentials_content):
                        st.rerun()
    
    # Main content - Danh sách stores
    st.header("📋 Danh sách Stores")
    
    stores = load_stores()
    
    if not stores:
        st.info("📝 Chưa có store nào. Hãy thêm store mới ở sidebar!")
    else:
        # Hiển thị danh sách stores
        for i, store in enumerate(stores):
            with st.expander(f"🏪 {store['store_name']} ({store['domain']})", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **Thông tin Store:**
                    - 🏪 **Tên**: {store['store_name']}
                    - 🌐 **Domain**: {store['domain']}
                    - 🆔 **Property ID**: {store['property_id']}
                    - 📅 **Tạo lúc**: {store['created_at']}
                    """)
                    
                    if store['last_used']:
                        st.markdown(f"- 🕒 **Sử dụng cuối**: {store['last_used']}")
                
                with col2:
                    # Nút sử dụng store
                    if st.button("🚀 Sử dụng", key=f"use_{store['id']}"):
                        # Export credentials file
                        credentials_path = export_store_credentials(store)
                        if credentials_path:
                            # Cập nhật thời gian sử dụng
                            update_last_used(store['id'])
                            
                            # Lưu thông tin vào session state để chuyển sang GA4 Analyzer
                            st.session_state['selected_store'] = {
                                'store_name': store['store_name'],
                                'domain': store['domain'],
                                'property_id': store['property_id'],
                                'credentials_path': credentials_path
                            }
                            
                            st.success(f"✅ Đã chọn store: {store['store_name']}")
                            st.info("💡 Chuyển sang tab GA4 Analyzer để phân tích dữ liệu")
                    
                    # Nút xóa store
                    if st.button("🗑️ Xóa", key=f"delete_{store['id']}"):
                        if delete_store(store['id']):
                            st.rerun()
        
        # Thống kê
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Tổng số stores", len(stores))
        with col2:
            used_stores = len([s for s in stores if s['last_used']])
            st.metric("🚀 Stores đã sử dụng", used_stores)
        with col3:
            unused_stores = len([s for s in stores if not s['last_used']])
            st.metric("📝 Stores chưa sử dụng", unused_stores)
    
    # Hướng dẫn sử dụng
    st.markdown("---")
    st.header("📖 Hướng dẫn sử dụng")
    
    st.markdown("""
    ### 🔧 Cách thêm store:
    1. **Nhập thông tin store** ở sidebar bên trái
    2. **Upload file credentials.json** từ Google Analytics
    3. **Nhấn "Thêm Store"** để lưu
    
    ### 🚀 Cách sử dụng store:
    1. **Chọn store** từ danh sách bên trên
    2. **Nhấn "Sử dụng"** để chọn store
    3. **Chuyển sang GA4 Analyzer** để phân tích dữ liệu
    
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
                export_data = []
                for store in stores:
                    export_data.append({
                        'store_name': store['store_name'],
                        'domain': store['domain'],
                        'property_id': store['property_id'],
                        'created_at': store['created_at'],
                        'last_used': store['last_used']
                    })
                
                # Tạo file download
                import io
                buffer = io.StringIO()
                json.dump(export_data, buffer, ensure_ascii=False, indent=2)
                buffer.seek(0)
                
                st.download_button(
                    label="📥 Tải file Export",
                    data=buffer.getvalue(),
                    file_name=f"ga4_stores_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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