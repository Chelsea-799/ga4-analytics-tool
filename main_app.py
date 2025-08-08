#!/usr/bin/env python3
"""
GA4 Analytics Tool - Main Application
"""

import streamlit as st
import json
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="GA4 + Google Ads Analytics Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .menu-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: white;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    .menu-card:hover {
        transform: translateY(-5px);
    }
    .stats-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 GA4 + Google Ads Analytics Tool</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Phân tích toàn diện dữ liệu GA4 và Google Ads cho doanh nghiệp</p>', unsafe_allow_html=True)
    
    # Load stores data
    stores_data = {}
    if os.path.exists('stores_data.json'):
        try:
            with open('stores_data.json', 'r', encoding='utf-8') as f:
                stores_data = json.load(f)
        except:
            stores_data = {}
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stats-card">
            <h3>🏪 Stores</h3>
            <h2>{}</h2>
        </div>
        """.format(len(stores_data)), unsafe_allow_html=True)
    
    with col2:
        ga4_count = sum(1 for store in stores_data.values() if store.get('ga4_property_id'))
        st.markdown("""
        <div class="stats-card">
            <h3>📈 GA4 Properties</h3>
            <h2>{}</h2>
        </div>
        """.format(ga4_count), unsafe_allow_html=True)
    
    with col3:
        ads_count = sum(1 for store in stores_data.values() if store.get('google_ads_customer_id'))
        st.markdown("""
        <div class="stats-card">
            <h3>📢 Google Ads</h3>
            <h2>{}</h2>
        </div>
        """.format(ads_count), unsafe_allow_html=True)
    
    with col4:
        data_files = len([f for f in os.listdir('data') if f.endswith('.json')]) if os.path.exists('data') else 0
        st.markdown("""
        <div class="stats-card">
            <h3>💾 Data Files</h3>
            <h2>{}</h2>
        </div>
        """.format(data_files), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Main Menu
    st.markdown("## 🎯 Chọn chức năng phân tích:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏪 Store Manager", use_container_width=True):
            st.switch_page("pages/1_🏪_Store_Manager.py")
        
        if st.button("🔍 GA4 Analyzer", use_container_width=True):
            st.switch_page("pages/2_🔍_GA4_Analyzer.py")
    
    with col2:
        if st.button("📢 Google Ads Analyzer", use_container_width=True):
            st.switch_page("pages/3_📢_Google_Ads_Analyzer.py")
        
        if st.button("📊 GA4 + Ads Analyzer", use_container_width=True):
            st.switch_page("pages/4_📊_GA4_+_Ads_Analyzer.py")
    
    # Recent Activity
    st.markdown("---")
    st.markdown("## 📋 Hoạt động gần đây:")
    
    if stores_data:
        for store_name, store_data in list(stores_data.items())[:3]:
            with st.expander(f"🏪 {store_name}"):
                col1, col2 = st.columns(2)
                with col1:
                    if store_data.get('ga4_property_id'):
                        st.success("✅ GA4: Đã cấu hình")
                    else:
                        st.warning("⚠️ GA4: Chưa cấu hình")
                
                with col2:
                    if store_data.get('google_ads_customer_id'):
                        st.success("✅ Google Ads: Đã cấu hình")
                    else:
                        st.warning("⚠️ Google Ads: Chưa cấu hình")
    else:
        st.info("📝 Chưa có store nào được cấu hình. Hãy vào Store Manager để thêm store đầu tiên!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🔄 Tự động deploy trên Streamlit Cloud | 📊 Phân tích dữ liệu thời gian thực</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 