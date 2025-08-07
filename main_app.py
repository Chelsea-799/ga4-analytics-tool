#!/usr/bin/env python3
"""
GA4 Analytics Tool - Main Application
"""

import streamlit as st
import os

# Cấu hình trang
st.set_page_config(
    page_title="GA4 Analytics Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Hàm chính"""
    st.title("📊 GA4 Analytics Tool")
    st.markdown("Tool phân tích Google Analytics 4 với AI")
    st.markdown("---")
    
    # Navigation
    st.header("🎯 Chọn Tool")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏪 Store Manager")
        st.markdown("""
        **Quản lý thông tin store:**
        - ➕ Thêm store mới
        - 📋 Xem danh sách stores
        - 🚀 Chọn store để phân tích
        - 📤 Export/Import dữ liệu
        """)
        
        if st.button("🏪 Mở Store Manager", use_container_width=True):
            st.switch_page("pages/1_🏪_Store_Manager.py")
    
    with col2:
        st.subheader("🔍 GA4 Analyzer")
        st.markdown("""
        **Phân tích dữ liệu GA4:**
        - 📈 Chỉ số cơ bản
        - 📦 Dữ liệu sản phẩm
        - 🤖 Phân tích AI
        - 📊 Báo cáo chi tiết
        """)
        
        if st.button("🔍 Mở GA4 Analyzer", use_container_width=True):
            st.switch_page("pages/2_🔍_GA4_Analyzer.py")
    
    # Thống kê
    st.markdown("---")
    st.header("📊 Thống kê")
    
    # Kiểm tra file stores
    stores_file = "stores_data.json"
    if os.path.exists(stores_file):
        try:
            import json
            with open(stores_file, 'r', encoding='utf-8') as f:
                stores = json.load(f)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Tổng số stores", len(stores))
            with col2:
                used_stores = len([s for s in stores if s.get('last_used')])
                st.metric("🚀 Stores đã sử dụng", used_stores)
            with col3:
                unused_stores = len([s for s in stores if not s.get('last_used')])
                st.metric("📝 Stores chưa sử dụng", unused_stores)
        except:
            st.info("📝 Chưa có stores nào")
    else:
        st.info("📝 Chưa có stores nào")
    
    # Hướng dẫn sử dụng
    st.markdown("---")
    st.header("📖 Hướng dẫn sử dụng")
    
    st.markdown("""
    ### 🔧 Bước 1: Quản lý Store
    1. **Mở Store Manager** để thêm stores
    2. **Nhập thông tin store**: Tên, Domain, Property ID
    3. **Upload file credentials.json** từ Google Analytics
    4. **Lưu store** để sử dụng sau này
    
    ### 🚀 Bước 2: Phân tích dữ liệu
    1. **Mở GA4 Analyzer** để phân tích
    2. **Chọn store** từ danh sách đã lưu
    3. **Nhập OpenAI API key** (nếu muốn phân tích AI)
    4. **Chọn thời gian phân tích** (số ngày)
    5. **Xem kết quả** phân tích
    
    ### 📊 Tính năng chính:
    - **Store Manager**: Quản lý thông tin store
    - **GA4 Analyzer**: Phân tích dữ liệu với AI
    - **Lưu trữ an toàn**: Credentials được mã hóa
    - **Export/Import**: Chuyển dữ liệu giữa các máy
    """)
    
    # Thông tin về API keys
    st.markdown("---")
    st.header("🔑 API Keys")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 GA4 Credentials")
        st.markdown("""
        **Cách lấy file credentials.json:**
        1. Vào Google Cloud Console
        2. Tạo Service Account
        3. Tạo key JSON
        4. Cấp quyền cho GA4 Property
        5. Download file credentials.json
        """)
    
    with col2:
        st.subheader("🤖 OpenAI API Key")
        st.markdown("""
        **Cách lấy OpenAI API key:**
        1. Đăng ký tài khoản OpenAI
        2. Vào API Keys section
        3. Tạo API key mới
        4. Copy key để sử dụng
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📊 GA4 Analytics Tool - Powered by Streamlit & OpenAI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 