#!/usr/bin/env python3
"""
Marketing Analytics Hub - Entry Module
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
import tempfile

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
    
    # Load stores data with backward-compatible normalization
    stores_data = {}
    if os.path.exists('stores_data.json'):
        try:
            with open('stores_data.json', 'r', encoding='utf-8') as f:
                raw = json.load(f)
            # Normalize legacy list structure -> dict keyed by store_name
            if isinstance(raw, list):
                normalized = {}
                for s in raw:
                    name = s.get('store_name') or s.get('name') or f"store_{s.get('id','')}"
                    normalized[name] = {
                        'store_name': s.get('store_name', name),
                        'domain': s.get('domain'),
                        'created_at': s.get('created_at'),
                        'last_used': s.get('last_used'),
                        # GA4 keys mapping
                        'ga4_property_id': s.get('property_id') or s.get('ga4_property_id'),
                        'ga4_credentials_content': s.get('credentials_content') or s.get('ga4_credentials_content'),
                        # Google Ads keys (if already present in file)
                        'google_ads_customer_id': s.get('google_ads_customer_id'),
                        'google_ads_developer_token': s.get('google_ads_developer_token'),
                        'google_ads_client_id': s.get('google_ads_client_id'),
                        'google_ads_client_secret': s.get('google_ads_client_secret'),
                        'google_ads_refresh_token': s.get('google_ads_refresh_token'),
                    }
                stores_data = normalized
                # Try to persist normalized structure for future runs
                try:
                    with open('stores_data.json', 'w', encoding='utf-8') as wf:
                        json.dump(stores_data, wf, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            elif isinstance(raw, dict):
                stores_data = raw
            else:
                stores_data = {}
        except Exception:
            stores_data = {}
    
    # Date range for REST product counts
    try:
        today = datetime.now().date()
        default_start = (today - timedelta(days=29))
        default_end = today
        start_date, end_date = st.date_input(
            "Khoảng ngày cho số lượng sản phẩm (REST)",
            (default_start, default_end),
        )
    except Exception:
        start_date, end_date = None, None

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
        # Count stores with Google Ads data (JSON files or Google Sheets config)
        ads_count = 0
        if os.path.exists('data'):
            for store_name in stores_data.keys():
                # Check for JSON files
                json_files = [f for f in os.listdir('data') if f.startswith(f'google_ads_{store_name}') and f.endswith('.json')]
                if json_files:
                    ads_count += 1
                    continue
                
                # Check for Google Sheets config
                sheets_config = f"data/sheets_config_{store_name}.json"
                if os.path.exists(sheets_config):
                    ads_count += 1
        
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
    
    # Only REST API-based product counts are supported (no catalog JSON/Sheets)

    @st.cache_data(ttl=600)
    def fetch_product_count_via_rest(
        url_template: str,
        headers_txt: str | None,
        count_field_path: str | None,
        header_key: str | None,
        domain_value: str | None,
        start_date_str: str | None,
        end_date_str: str | None,
        auth_type: str | None,
        token: str | None,
        client_id: str | None,
        client_secret: str | None,
        basic_user: str | None,
        basic_pass: str | None,
    ) -> int | None:
        try:
            import requests  # local import to avoid hard dep if unused
        except Exception:
            return None
        if not url_template:
            return None

        # Build URL with optional placeholders
        mapping = {
            'domain': (domain_value or '').rstrip('/'),
            'start_date': start_date_str or '',
            'end_date': end_date_str or '',
        }
        try:
            url = url_template.format(**mapping)
        except Exception:
            url = url_template

        headers_txt = headers_txt or ''
        headers = {}
        if headers_txt:
            try:
                headers = json.loads(headers_txt)
            except Exception:
                headers = {}
        # Compose auth headers from stored auth config if provided
        try:
            if auth_type == 'Bearer' and token:
                headers.setdefault('Authorization', f'Bearer {token}')
            elif auth_type == 'Basic' and basic_user is not None and basic_pass is not None:
                import base64
                b = base64.b64encode(f"{basic_user}:{basic_pass}".encode('utf-8')).decode('utf-8')
                headers.setdefault('Authorization', f'Basic {b}')
            elif auth_type == 'ClientID/Secret' and client_id and client_secret:
                headers.setdefault('X-Client-Id', client_id)
                headers.setdefault('X-Client-Secret', client_secret)
        except Exception:
            pass
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            # Auto-detect WooCommerce header if not provided
            auto_header = header_key
            if not auto_header and ('/wp-json/wc/' in url.lower()):
                auto_header = 'X-WP-Total'
            # Try header-based total (e.g., WooCommerce X-WP-Total)
            if auto_header:
                val = resp.headers.get(auto_header)
                if val is not None and str(val).strip().isdigit():
                    return int(val)
            data = resp.json()
            # Follow dot-path in JSON payload if provided, e.g., "data.total" or "total_count"
            path = (count_field_path or '').strip()
            if path:
                cur = data
                for part in path.split('.'):
                    if isinstance(cur, dict) and part in cur:
                        cur = cur[part]
                    else:
                        cur = None
                        break
                if isinstance(cur, (int, float)):
                    return int(cur)
            # Fallback common fields
            for key in ['count','total','total_count']:
                if isinstance(data, dict) and key in data and isinstance(data[key], (int, float)):
                    return int(data[key])
            return None
        except Exception:
            return None

    if stores_data:
        for store_name, store_data in list(stores_data.items())[:3]:
            with st.expander(f"🏪 {store_name}"):
                col1, col2 = st.columns(2)
                with col1:
                    if store_data.get('ga4_property_id'):
                        st.success("✅ GA4: Đã cấu hình")
                    else:
                        st.warning("⚠️ GA4: Chưa cấu hình")
                    # REST product count only
                    try:
                        rest_total = None
                        # Dựng URL tự động nếu là Woo và không có URL
                        auto_url = store_data.get('product_count_api_url')
                        if not auto_url and store_data.get('domain') and store_data.get('product_count_woo_ck') and store_data.get('product_count_woo_cs'):
                            dom = str(store_data.get('domain')).rstrip('/')
                            # Đảm bảo có scheme để gọi requests hợp lệ
                            if not dom.startswith('http://') and not dom.startswith('https://'):
                                dom = f"https://{dom}"
                            ck = store_data.get('product_count_woo_ck')
                            cs = store_data.get('product_count_woo_cs')
                            auto_url = f"{dom}/wp-json/wc/v3/products?status=publish&per_page=1&consumer_key={ck}&consumer_secret={cs}"

                        if auto_url:
                            start_str = start_date.strftime('%Y-%m-%d') if start_date else None
                            end_str = end_date.strftime('%Y-%m-%d') if end_date else None
                            rest_total = fetch_product_count_via_rest(
                                auto_url,
                                store_data.get('product_count_api_headers'),
                                store_data.get('product_count_count_field'),
                                store_data.get('product_count_header_key'),
                                store_data.get('domain'),
                                start_str,
                                end_str,
                                store_data.get('product_count_auth_type'),
                                store_data.get('product_count_api_token'),
                                store_data.get('product_count_client_id'),
                                store_data.get('product_count_client_secret'),
                                store_data.get('product_count_basic_user'),
                                store_data.get('product_count_basic_pass'),
                            )
                        if rest_total is not None:
                            st.info(f"🛍️ Products: {rest_total:,}")
                        else:
                            st.caption("🛍️ Products: chưa cấu hình REST API hoặc không đọc được")
                    except Exception:
                        st.caption("🛍️ Products: lỗi khi gọi REST API")
                
                with col2:
                    # Check if Google Ads data exists (JSON files or Google Sheets config)
                    ads_data_exists = False
                    if os.path.exists('data'):
                        # Check for JSON files
                        json_files = [f for f in os.listdir('data') if f.startswith(f'google_ads_{store_name}') and f.endswith('.json')]
                        if json_files:
                            ads_data_exists = True
                        
                        # Check for Google Sheets config
                        sheets_config = f"data/sheets_config_{store_name}.json"
                        if os.path.exists(sheets_config):
                            ads_data_exists = True
                    
                    if ads_data_exists:
                        st.success("✅ Google Ads: Có dữ liệu (JSON/Sheets)")
                    else:
                        st.info("📢 Google Ads: Chưa có dữ liệu (cần upload JSON hoặc setup Google Sheets)")
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