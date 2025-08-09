#!/usr/bin/env python3
"""
GA4 + Google Ads Combined Analyzer - Phân tích kết hợp GA4 và Google Ads
"""

import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import tempfile
import numpy as np
import gspread
from google.oauth2 import service_account
import re

# Cấu hình trang
st.set_page_config(
    page_title="GA4 + Ads Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_stores():
    """Load stores data với backward compatibility"""
    try:
        with open('stores_data.json', 'r', encoding='utf-8') as f:
            stores_data = json.load(f)
        
        # Backward compatibility: nếu là list thì convert thành dict
        if isinstance(stores_data, list):
            stores_dict = {}
            for store in stores_data:
                stores_dict[store['store_name']] = store
            return stores_dict
        else:
            return stores_data
    except Exception as e:
        st.error(f"❌ Lỗi load stores: {e}")
        return {}

def get_ga4_data_file(store_name):
    """Lấy file dữ liệu GA4 cho store"""
    return f"data/ga4_{store_name}.json"

def get_ads_data_file(store_name):
    """Lấy file dữ liệu Google Ads cho store"""
    return f"data/google_ads_{store_name}.json"

def get_google_sheets_config(store_name):
    """Lấy cấu hình Google Sheets cho store"""
    return f"data/sheets_config_{store_name}.json"

def connect_google_sheets(credentials_content, spreadsheet_id, sheet_name):
    """Kết nối Google Sheets và lấy dữ liệu"""
    try:
        # Tạo credentials từ JSON content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            tmp_file.write(credentials_content.encode('utf-8'))
            credentials_path = tmp_file.name

        # Kết nối Google Sheets với scopes chuẩn
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
        ]
        credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
        client = gspread.authorize(credentials)

        # Mở spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Cố mở worksheet theo tên, nếu không có thì fallback sheet đầu tiên
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.sheet1
            st.warning(f"🔁 Không tìm thấy sheet '{sheet_name}'. Đã dùng sheet đầu tiên: '{worksheet.title}'.")

        # Lấy toàn bộ values và tự xác định hàng header hợp lệ
        values = worksheet.get_all_values()
        if not values:
            return []

        header_row_idx = 0
        for i, row in enumerate(values[:10]):
            non_empty = [c for c in row if str(c).strip() != '']
            if len(non_empty) >= 2 and len(set(map(lambda x: str(x).strip().lower(), non_empty))) == len(non_empty):
                header_row_idx = i
                break

        raw_headers = values[header_row_idx]

        alias_map = {
            'date': 'date',
            'ngày': 'date',
            'campaign': 'campaign',
            'impr.': 'impressions',
            'impr': 'impressions',
            'impressions': 'impressions',
            'clicks': 'clicks',
            'cost': 'cost',
            'spend': 'cost',
            'conversions': 'conversions',
            'conv. value': 'conversion_value',
            'conversion value': 'conversion_value',
            'value': 'conversion_value',
            'ctr': 'ctr',
            'avg. cpc': 'avg_cpc',
            'cpc': 'avg_cpc'
        }

        def normalize_header(h):
            key = str(h).strip().lower()
            return alias_map.get(key, key)

        headers = [normalize_header(h) if str(h).strip() else f"col_{idx+1}" for idx, h in enumerate(raw_headers)]

        records = []
        for row in values[header_row_idx+1:]:
            if all(str(c).strip() == '' for c in row):
                continue
            padded = row + [''] * (len(headers) - len(row))
            record = {headers[i]: padded[i] for i in range(len(headers))}
            records.append(record)

        return records

    except Exception as e:
        message = str(e)
        if 'has not been used in project' in message or 'disabled' in message:
            st.error("❌ Google Sheets API/Drive API chưa được bật cho project Service Account.")
        elif 'The caller does not have permission' in message or 'Permission' in message:
            st.error("❌ Service Account chưa được chia sẻ quyền Editor với Google Sheet này.")
        else:
            st.error(f"❌ Lỗi kết nối Google Sheets: {message}")
        return None
    finally:
        try:
            if 'credentials_path' in locals() and os.path.exists(credentials_path):
                os.unlink(credentials_path)
        except Exception:
            pass

def load_ga4_data(store_name):
    """Load dữ liệu GA4 từ file JSON"""
    data_file = get_ga4_data_file(store_name)
    
    if not os.path.exists(data_file):
        st.warning(f"⚠️ Chưa có file dữ liệu GA4: {data_file}")
        return pd.DataFrame()
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            st.warning("⚠️ File dữ liệu GA4 trống")
            return pd.DataFrame()
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"❌ Lỗi load dữ liệu GA4: {e}")
        return pd.DataFrame()

def save_ads_data_to_json(store_name, df):
    """Lưu dữ liệu Google Ads vào JSON file để backup"""
    if df.empty:
        return False
    
    try:
        data_file = get_ads_data_file(store_name)
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        
        # Convert DataFrame to JSON
        data = df.to_dict('records')
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ Đã lưu {len(data)} records vào {data_file}")
        return True
        
    except Exception as e:
        st.error(f"❌ Lỗi lưu JSON file: {e}")
        return False

def load_ads_data_from_sheets(store_name):
    """Load dữ liệu Google Ads từ Google Sheets"""
    config_file = get_google_sheets_config(store_name)
    
    if not os.path.exists(config_file):
        st.warning(f"⚠️ Chưa có cấu hình Google Sheets: {config_file}")
        return pd.DataFrame()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Kết nối và lấy dữ liệu từ Google Sheets
        data = connect_google_sheets(
            config['credentials_content'],
            config['spreadsheet_id'],
            config['sheet_name']
        )
        
        if data is None:
            return pd.DataFrame()
        
        # Convert thành DataFrame và chuẩn hóa số liệu
        df = pd.DataFrame(data)

        def smart_to_float(x):
            if isinstance(x, (int, float)):
                return float(x)
            s = str(x).strip()
            if s == '':
                return 0.0
            s = re.sub(r'[^0-9,.-]', '', s)
            if ',' in s and '.' in s:
                if s.rfind(',') > s.rfind('.'):
                    s = s.replace('.', '').replace(',', '.')
                else:
                    s = s.replace(',', '')
            else:
                if ',' in s:
                    s = s.replace(',', '.')
            try:
                return float(s)
            except Exception:
                return 0.0

        numeric_fields = ['impressions', 'clicks', 'cost', 'conversions', 'conversion_value', 'ctr', 'avg_cpc']
        for col in numeric_fields:
            if col in df.columns:
                df[col] = df[col].apply(smart_to_float)
        
        # Auto save to JSON file
        save_ads_data_to_json(store_name, df)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Lỗi load dữ liệu từ Google Sheets: {e}")
        return pd.DataFrame()

def auto_import_json_files(store_name):
    """Tự động import JSON files từ thư mục data/"""
    import glob
    
    # Tìm tất cả JSON files cho store này
    pattern = f"data/google_ads_{store_name}_*.json"
    json_files = glob.glob(pattern)
    
    if not json_files:
        return pd.DataFrame()
    
    # Lấy file mới nhất
    latest_file = max(json_files, key=os.path.getctime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        
        # Auto save vào file chính
        main_file = get_ads_data_file(store_name)
        os.makedirs(os.path.dirname(main_file), exist_ok=True)
        
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ Auto import: {len(data)} records từ {os.path.basename(latest_file)}")
        return df
        
    except Exception as e:
        st.error(f"❌ Lỗi auto import JSON: {e}")
        return pd.DataFrame()

def load_ads_data(store_name):
    """Load dữ liệu Google Ads (ưu tiên Google Sheets, fallback JSON file, auto import)"""
    # Thử load từ Google Sheets trước
    df = load_ads_data_from_sheets(store_name)
    
    if not df.empty:
        return df
    
    # Thử auto import JSON files
    df = auto_import_json_files(store_name)
    
    if not df.empty:
        return df
    
    # Fallback: load từ JSON file chính
    data_file = get_ads_data_file(store_name)
    
    if not os.path.exists(data_file):
        st.warning(f"⚠️ Chưa có file dữ liệu Google Ads: {data_file}")
        return pd.DataFrame()
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            st.warning("⚠️ File dữ liệu Google Ads trống")
            return pd.DataFrame()
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"❌ Lỗi load dữ liệu Google Ads: {e}")
        return pd.DataFrame()

def analyze_combined_data(ga4_df, ads_df):
    """Phân tích dữ liệu kết hợp GA4 và Google Ads"""
    if ga4_df.empty and ads_df.empty:
        return {}
    
    # GA4 metrics
    ga4_metrics = {}
    if not ga4_df.empty:
        if 'totalRevenue' in ga4_df.columns:
            ga4_metrics['total_revenue'] = ga4_df['totalRevenue'].sum()
        if 'transactions' in ga4_df.columns:
            ga4_metrics['total_transactions'] = ga4_df['transactions'].sum()
        if 'totalUsers' in ga4_df.columns:
            ga4_metrics['total_users'] = ga4_df['totalUsers'].sum()
        if 'sessions' in ga4_df.columns:
            ga4_metrics['total_sessions'] = ga4_df['sessions'].sum()
    
    # Google Ads metrics
    ads_metrics = {}
    if not ads_df.empty:
        if 'cost' in ads_df.columns:
            ads_metrics['total_cost'] = ads_df['cost'].sum()
        if 'clicks' in ads_df.columns:
            ads_metrics['total_clicks'] = ads_df['clicks'].sum()
        if 'impressions' in ads_df.columns:
            ads_metrics['total_impressions'] = ads_df['impressions'].sum()
        if 'conversions' in ads_df.columns:
            ads_metrics['total_conversions'] = ads_df['conversions'].sum()
        if 'conversion_value' in ads_df.columns:
            ads_metrics['total_conversion_value'] = ads_df['conversion_value'].sum()
    
    # Combined metrics
    combined_metrics = {}
    
    # ROAS (Return on Ad Spend)
    if ads_metrics.get('total_cost', 0) > 0 and ga4_metrics.get('total_revenue', 0) > 0:
        combined_metrics['roas'] = ga4_metrics['total_revenue'] / ads_metrics['total_cost']
    else:
        combined_metrics['roas'] = 0
    
    # Cost per Conversion
    if ads_metrics.get('total_cost', 0) > 0 and ads_metrics.get('total_conversions', 0) > 0:
        combined_metrics['cost_per_conversion'] = ads_metrics['total_cost'] / ads_metrics['total_conversions']
    else:
        combined_metrics['cost_per_conversion'] = 0
    
    # Conversion Rate
    if ads_metrics.get('total_clicks', 0) > 0 and ads_metrics.get('total_conversions', 0) > 0:
        combined_metrics['conversion_rate'] = (ads_metrics['total_conversions'] / ads_metrics['total_clicks']) * 100
    else:
        combined_metrics['conversion_rate'] = 0
    
    # CTR
    if ads_metrics.get('total_impressions', 0) > 0 and ads_metrics.get('total_clicks', 0) > 0:
        combined_metrics['ctr'] = (ads_metrics['total_clicks'] / ads_metrics['total_impressions']) * 100
    else:
        combined_metrics['ctr'] = 0
    
    return {
        'ga4': ga4_metrics,
        'ads': ads_metrics,
        'combined': combined_metrics
    }

def create_demo_data():
    """Tạo dữ liệu demo cho GA4 và Google Ads"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    
    # GA4 demo data
    ga4_demo = []
    for date in dates:
        ga4_demo.append({
            'date': date.strftime('%Y-%m-%d'),
            'totalUsers': np.random.randint(100, 1000),
            'sessions': np.random.randint(150, 1500),
            'screenPageViews': np.random.randint(300, 3000),
            'transactions': np.random.randint(5, 50),
            'totalRevenue': round(np.random.uniform(500, 5000), 2)
        })
    
    # Google Ads demo data
    campaigns = ["Brand Campaign", "Product Search", "Retargeting"]
    ads_demo = []
    for date in dates:
        for campaign in campaigns:
            impressions = np.random.randint(1000, 10000)
            clicks = np.random.randint(50, int(impressions * 0.1))
            cost = np.random.uniform(50, 500)
            conversions = np.random.randint(0, int(clicks * 0.3))
            conversion_value = conversions * np.random.uniform(100, 300)
            
            ads_demo.append({
                'date': date.strftime('%Y-%m-%d'),
                'campaign': campaign,
                'impressions': impressions,
                'clicks': clicks,
                'cost': round(cost, 2),
                'conversions': conversions,
                'conversion_value': round(conversion_value, 2)
            })
    
    return ga4_demo, ads_demo

def main():
    """Hàm chính"""
    st.title("📊 GA4 + Google Ads Analyzer - Phân tích kết hợp")
    st.markdown("---")
    
    # Load stores
    stores = load_stores()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        
        # Chọn store
        if stores:
            store_names = list(stores.keys())
            selected_store_name = st.selectbox(
                "🏪 Chọn Store",
                store_names,
                index=0
            )
            
            selected_store = stores[selected_store_name]
            st.success(f"✅ Store: {selected_store_name}")
            
            # Kiểm tra config
            ga4_property_id = selected_store.get('ga4_property_id') or selected_store.get('property_id')

            if ga4_property_id:
                st.info(f"🆔 GA4 Property ID: {ga4_property_id}")
            else:
                st.warning("⚠️ Chưa có GA4 config")

            # Trạng thái Google Ads theo Sheets/JSON
            config_file = get_google_sheets_config(selected_store_name)
            data_file = get_ads_data_file(selected_store_name)

            if os.path.exists(config_file):
                st.success("✅ Google Sheets: Đã cấu hình")
            else:
                st.info("📄 Google Sheets: Chưa cấu hình")

            if os.path.exists(data_file):
                st.success("✅ Google Ads JSON: Có dữ liệu")
            else:
                st.info("📁 Google Ads JSON: Chưa có dữ liệu")
        else:
            st.warning("⚠️ Chưa có stores nào")
            st.info("💡 Vào Store Manager để thêm store")
            if st.button("🏪 Mở Store Manager"):
                st.switch_page("pages/1_🏪_Store_Manager.py")
            return
        
        st.markdown("---")
        
        # Tùy chọn: Fetch GA4 now (Cách A - tự động)
        if selected_store.get('ga4_property_id') and selected_store.get('ga4_credentials_content'):
            with st.expander("⚡ Fetch GA4 now (Cách A - tự động)"):
                fetch_days = st.slider("Số ngày", min_value=7, max_value=180, value=30)
                if st.button("📥 Lấy dữ liệu GA4 và lưu JSON"):
                    try:
                        # Gọi GA4 API nhanh gọn tại đây
                        from google.analytics.data_v1beta import BetaAnalyticsDataClient
                        from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
                        from google.oauth2 import service_account
                        import tempfile

                        # Tạo file credentials tạm
                        cred_content = selected_store['ga4_credentials_content']
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as tmp_file:
                            tmp_file.write(cred_content)
                            cred_path = tmp_file.name

                        credentials = service_account.Credentials.from_service_account_file(cred_path)
                        client = BetaAnalyticsDataClient(credentials=credentials)
                        property_id = str(selected_store.get('ga4_property_id'))
                        req = RunReportRequest(
                            property=f"properties/{property_id}",
                            dimensions=[Dimension(name="date")],
                            metrics=[
                                Metric(name="totalUsers"),
                                Metric(name="sessions"),
                                Metric(name="screenPageViews"),
                                Metric(name="transactions"),
                                Metric(name="totalRevenue"),
                            ],
                            date_ranges=[DateRange(start_date=f"{fetch_days}daysAgo", end_date="today")],
                        )
                        resp = client.run_report(req)
                        rows = []
                        for r in resp.rows:
                            rows.append({
                                "date": r.dimension_values[0].value,
                                "totalUsers": int(r.metric_values[0].value or 0),
                                "sessions": int(r.metric_values[1].value or 0),
                                "screenPageViews": int(r.metric_values[2].value or 0),
                                "transactions": int(r.metric_values[3].value or 0),
                                "totalRevenue": float(r.metric_values[4].value or 0.0),
                            })
                        os.makedirs('data', exist_ok=True)
                        out_path = os.path.join('data', f"ga4_{selected_store_name}.json")
                        with open(out_path, 'w', encoding='utf-8') as f:
                            json.dump(rows, f, ensure_ascii=False, indent=2)
                        st.success(f"✅ Đã fetch và lưu GA4 vào {out_path}")
                    except Exception as e:
                        st.error(f"❌ Lỗi fetch GA4: {e}")
                    finally:
                        try:
                            if 'cred_path' in locals() and os.path.exists(cred_path):
                                os.unlink(cred_path)
                        except Exception:
                            pass

        # Upload files
        st.subheader("📁 Upload dữ liệu")
        
        # Upload GA4 data
        st.markdown("**📊 GA4 Data:**")
        ga4_upload = st.file_uploader(
            "GA4 JSON file",
            type=['json'],
            key="ga4_upload"
        )
        
        if ga4_upload is not None:
            try:
                data = json.load(ga4_upload)
                data_file = get_ga4_data_file(selected_store_name)
                os.makedirs(os.path.dirname(data_file), exist_ok=True)
                
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                st.success(f"✅ Đã lưu GA4 data: {data_file}")
                
            except Exception as e:
                st.error(f"❌ Lỗi xử lý GA4 file: {e}")
        
        # Upload Google Ads data
        st.markdown("**📢 Google Ads Data:**")
        ads_upload = st.file_uploader(
            "Google Ads JSON file",
            type=['json'],
            key="ads_upload"
        )
        
        if ads_upload is not None:
            try:
                data = json.load(ads_upload)
                data_file = get_ads_data_file(selected_store_name)
                os.makedirs(os.path.dirname(data_file), exist_ok=True)
                
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                st.success(f"✅ Đã lưu Google Ads data: {data_file}")
                
            except Exception as e:
                st.error(f"❌ Lỗi xử lý Google Ads file: {e}")
        
        # Tạo demo data
        st.markdown("---")
        st.subheader("🧪 Demo Data")
        if st.button("🎲 Tạo dữ liệu demo"):
            ga4_demo, ads_demo = create_demo_data()
            
            # Lưu GA4 demo
            ga4_file = get_ga4_data_file(selected_store_name)
            os.makedirs(os.path.dirname(ga4_file), exist_ok=True)
            with open(ga4_file, 'w', encoding='utf-8') as f:
                json.dump(ga4_demo, f, indent=2, ensure_ascii=False)
            
            # Lưu Google Ads demo
            ads_file = get_ads_data_file(selected_store_name)
            os.makedirs(os.path.dirname(ads_file), exist_ok=True)
            with open(ads_file, 'w', encoding='utf-8') as f:
                json.dump(ads_demo, f, indent=2, ensure_ascii=False)
            
            st.success("✅ Đã tạo dữ liệu demo!")
            st.rerun()
    
    # Main content
    if 'selected_store' in locals():
        st.header(f"📊 Phân tích kết hợp - {selected_store_name}")
        
        # Load dữ liệu
        ga4_df = load_ga4_data(selected_store_name)
        ads_df = load_ads_data(selected_store_name)
        
        if not ga4_df.empty or not ads_df.empty:
            # Phân tích kết hợp
            combined_metrics = analyze_combined_data(ga4_df, ads_df)
            
            # Hiển thị metrics tổng quan
            st.subheader("📈 Metrics tổng quan")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if combined_metrics.get('ga4', {}).get('total_revenue'):
                    st.metric("💰 Revenue (GA4)", f"${combined_metrics['ga4']['total_revenue']:,.2f}")
                if combined_metrics.get('ads', {}).get('total_cost'):
                    st.metric("💸 Cost (Ads)", f"${combined_metrics['ads']['total_cost']:,.2f}")
            
            with col2:
                if combined_metrics.get('combined', {}).get('roas'):
                    st.metric("💎 ROAS", f"{combined_metrics['combined']['roas']:.2f}x")
                if combined_metrics.get('combined', {}).get('cost_per_conversion'):
                    st.metric("🎯 Cost/Conv", f"${combined_metrics['combined']['cost_per_conversion']:.2f}")
            
            with col3:
                if combined_metrics.get('combined', {}).get('conversion_rate'):
                    st.metric("📊 Conv. Rate", f"{combined_metrics['combined']['conversion_rate']:.2f}%")
                if combined_metrics.get('combined', {}).get('ctr'):
                    st.metric("👁️ CTR", f"{combined_metrics['combined']['ctr']:.2f}%")
            
            with col4:
                if combined_metrics.get('ga4', {}).get('total_transactions'):
                    st.metric("🛒 Transactions", f"{combined_metrics['ga4']['total_transactions']:,}")
                if combined_metrics.get('ads', {}).get('total_clicks'):
                    st.metric("🖱️ Clicks", f"{combined_metrics['ads']['total_clicks']:,}")
            
            # Biểu đồ so sánh Revenue vs Cost
            if not ga4_df.empty and not ads_df.empty and 'date' in ga4_df.columns and 'date' in ads_df.columns:
                st.subheader("📊 So sánh Revenue vs Cost theo thời gian")
                
                # Chuẩn bị dữ liệu
                ga4_df['date'] = pd.to_datetime(ga4_df['date'])
                ads_df['date'] = pd.to_datetime(ads_df['date'])
                
                # Group by date
                ga4_daily = ga4_df.groupby('date').agg({
                    'totalRevenue': 'sum',
                    'transactions': 'sum',
                    'totalUsers': 'sum'
                }).reset_index()
                
                ads_daily = ads_df.groupby('date').agg({
                    'cost': 'sum',
                    'clicks': 'sum',
                    'conversions': 'sum'
                }).reset_index()
                
                # Merge data
                combined_daily = ga4_daily.merge(ads_daily, on='date', how='outer').fillna(0)
                
                # Biểu đồ
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=combined_daily['date'],
                    y=combined_daily['totalRevenue'],
                    name='Revenue (GA4)',
                    yaxis='y'
                ))
                
                fig.add_trace(go.Scatter(
                    x=combined_daily['date'],
                    y=combined_daily['cost'],
                    name='Cost (Ads)',
                    yaxis='y'
                ))
                
                fig.update_layout(
                    title="Revenue vs Cost Trend",
                    xaxis_title="Ngày",
                    yaxis_title="Amount ($)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Bảng so sánh
                st.subheader("📋 Bảng so sánh chi tiết")
                display_df = combined_daily.copy()
                display_df['ROAS'] = (display_df['totalRevenue'] / display_df['cost']).fillna(0)
                display_df['Date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                
                display_columns = ['Date', 'totalRevenue', 'cost', 'ROAS', 'transactions', 'conversions']
                display_df = display_df[display_columns]
                display_df.columns = ['Ngày', 'Revenue ($)', 'Cost ($)', 'ROAS', 'Transactions', 'Conversions']
                display_df['Revenue ($)'] = display_df['Revenue ($)'].round(2)
                display_df['Cost ($)'] = display_df['Cost ($)'].round(2)
                display_df['ROAS'] = display_df['ROAS'].round(2)
                
                st.dataframe(display_df, use_container_width=True)
            
            # Hiển thị dữ liệu riêng biệt
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 GA4 Data")
                if not ga4_df.empty:
                    st.dataframe(ga4_df, use_container_width=True)
                else:
                    st.info("💡 Chưa có dữ liệu GA4")
            
            with col2:
                st.subheader("📢 Google Ads Data")
                if not ads_df.empty:
                    st.dataframe(ads_df, use_container_width=True)
                else:
                    st.info("💡 Chưa có dữ liệu Google Ads")
            
            # Export options
            st.subheader("📥 Export dữ liệu")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if not ga4_df.empty:
                    csv = ga4_df.to_csv(index=False)
                    st.download_button(
                        "📥 GA4 CSV",
                        csv,
                        file_name=f"ga4_{selected_store_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if not ads_df.empty:
                    csv = ads_df.to_csv(index=False)
                    st.download_button(
                        "📥 Ads CSV",
                        csv,
                        file_name=f"ads_{selected_store_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                if not ga4_df.empty and not ads_df.empty:
                    # Combined data
                    combined_data = {
                        'ga4': ga4_df.to_dict('records'),
                        'ads': ads_df.to_dict('records'),
                        'metrics': combined_metrics
                    }
                    json_str = json.dumps(combined_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        "📥 Combined JSON",
                        json_str,
                        file_name=f"combined_{selected_store_name}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
        
        else:
            st.info("💡 Chưa có dữ liệu để phân tích")
            st.markdown("""
            **Hướng dẫn:**
            
            1. **Upload dữ liệu GA4:**
               - Export từ GA4 → JSON format
               - Upload file JSON ở sidebar
            
            2. **Upload dữ liệu Google Ads:**
               - Export từ Google Ads → JSON format
               - Upload file JSON ở sidebar
            
            3. **Hoặc dùng demo data:**
               - Click "🎲 Tạo dữ liệu demo" ở sidebar
            """)

if __name__ == "__main__":
    main()
