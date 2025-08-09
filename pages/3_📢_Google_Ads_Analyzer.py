#!/usr/bin/env python3
"""
Google Ads Analyzer - Phân tích dữ liệu Google Ads từ Google Sheets tự động
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

# Cấu hình trang
st.set_page_config(
    page_title="Google Ads Analyzer",
    page_icon="📢",
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
                name = store.get('store_name') or store.get('name') or f"store_{store.get('id','')}"
                stores_dict[name] = store
            return stores_dict
        else:
            return stores_data
    except Exception as e:
        st.error(f"❌ Lỗi load stores: {e}")
        return {}

def get_cursor_file(store_name):
    """Lấy file cursor cho store"""
    return f"data/cursor_{store_name}.txt"

def get_ads_data_file(store_name):
    """Lấy file dữ liệu Google Ads cho store"""
    return f"data/google_ads_{store_name}.json"

def get_google_sheets_config(store_name):
    """Lấy cấu hình Google Sheets cho store"""
    return f"data/sheets_config_{store_name}.json"

def load_cursor(store_name):
    """Load cursor để track dữ liệu đã xử lý"""
    cursor_file = get_cursor_file(store_name)
    try:
        if os.path.exists(cursor_file):
            with open(cursor_file, 'r') as f:
                return int(f.read().strip())
        return 0
    except:
        return 0

def save_cursor(store_name, line_count):
    """Lưu cursor sau khi xử lý"""
    cursor_file = get_cursor_file(store_name)
    try:
        os.makedirs(os.path.dirname(cursor_file), exist_ok=True)
        with open(cursor_file, 'w') as f:
            f.write(str(line_count))
        return True
    except Exception as e:
        st.error(f"❌ Lỗi lưu cursor: {e}")
        return False

def connect_google_sheets(credentials_content, spreadsheet_id, sheet_name):
    """Kết nối Google Sheets và lấy dữ liệu"""
    try:
        # Tạo credentials từ JSON content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            tmp_file.write(credentials_content.encode('utf-8'))
            credentials_path = tmp_file.name
        
        # Kết nối Google Sheets
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scope)
        client = gspread.authorize(credentials)
        
        # Mở spreadsheet và sheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Lấy tất cả dữ liệu
        data = worksheet.get_all_records()
        
        # Xóa file tạm
        os.unlink(credentials_path)
        
        return data
        
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
        return None

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
        
        # Convert thành DataFrame
        df = pd.DataFrame(data)
        
        # Kiểm tra và xử lý dữ liệu mới
        current_cursor = load_cursor(store_name)
        if len(data) > current_cursor:
            new_data_count = len(data) - current_cursor
            st.success(f"🆕 Phát hiện {new_data_count} dòng dữ liệu mới từ Google Sheets!")
            
            # Auto save to JSON file
            save_ads_data_to_json(store_name, df)
            
            # Cập nhật cursor
            save_cursor(store_name, len(data))
        
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
        st.warning(f"⚠️ Chưa có file dữ liệu: {data_file}")
        st.info("💡 Khuyến nghị: cấu hình mục '📊 Google Sheets Integration' ở sidebar (dùng SyncWith) để tool tự sync, không cần JSON.")
        st.markdown("""
        **Nếu muốn dùng JSON (fallback):**
        1. Xuất dữ liệu Google Ads ra Google Sheets (SyncWith/Export bất kỳ)
        2. Tải về dạng JSON hoặc convert sang JSON
        3. Upload file JSON tại sidebar hoặc đặt vào thư mục `data/` với tên `google_ads_{store_name}_*.json` để tool tự import
        """)
        return pd.DataFrame()
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            st.warning("⚠️ File dữ liệu trống")
            return pd.DataFrame()
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"❌ Lỗi load dữ liệu: {e}")
        return pd.DataFrame()

def save_google_sheets_config(store_name, credentials_content, spreadsheet_id, sheet_name):
    """Lưu cấu hình Google Sheets"""
    config_file = get_google_sheets_config(store_name)
    try:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        config = {
            'credentials_content': credentials_content,
            'spreadsheet_id': spreadsheet_id,
            'sheet_name': sheet_name,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        st.error(f"❌ Lỗi lưu cấu hình Google Sheets: {e}")
        return False

def analyze_ads_performance(df):
    """Phân tích hiệu suất Google Ads"""
    if df.empty:
        return {}
    
    # Tính toán metrics
    total_impressions = df['impressions'].sum() if 'impressions' in df.columns else 0
    total_clicks = df['clicks'].sum() if 'clicks' in df.columns else 0
    total_cost = df['cost'].sum() if 'cost' in df.columns else 0
    total_conversions = df['conversions'].sum() if 'conversions' in df.columns else 0
    total_conversion_value = df['conversion_value'].sum() if 'conversion_value' in df.columns else 0
    
    # Tính toán rates
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
    cpm = (total_cost / total_impressions * 1000) if total_impressions > 0 else 0
    conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    roas = (total_conversion_value / total_cost) if total_cost > 0 else 0
    
    return {
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'total_cost': total_cost,
        'total_conversions': total_conversions,
        'total_conversion_value': total_conversion_value,
        'ctr': ctr,
        'cpc': cpc,
        'cpm': cpm,
        'conversion_rate': conversion_rate,
        'roas': roas
    }

def create_demo_ads_data():
    """Tạo dữ liệu demo cho Google Ads"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    
    campaigns = [
        "Brand Campaign",
        "Product Search",
        "Retargeting",
        "Shopping Campaign",
        "Display Network"
    ]
    
    demo_data = []
    for date in dates:
        for campaign in campaigns:
            impressions = np.random.randint(100, 5000)
            clicks = np.random.randint(5, int(impressions * 0.1))
            cost = np.random.uniform(10, 200)
            conversions = np.random.randint(0, int(clicks * 0.3))
            conversion_value = conversions * np.random.uniform(50, 200)
            
            demo_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'campaign': campaign,
                'impressions': impressions,
                'clicks': clicks,
                'cost': round(cost, 2),
                'conversions': conversions,
                'conversion_value': round(conversion_value, 2)
            })
    
    return demo_data

def main():
    """Hàm chính"""
    st.title("📢 Google Ads Analyzer - Phân tích dữ liệu Google Ads")
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
            
            # Trạng thái Google Ads dựa trên Sheets/JSON (không dùng API)
            config_file = get_google_sheets_config(selected_store_name)
            data_file = get_ads_data_file(selected_store_name)

            if os.path.exists(config_file):
                st.success("✅ Google Sheets: Đã cấu hình")
            else:
                st.info("📄 Google Sheets: Chưa cấu hình")

            if os.path.exists(data_file):
                st.success(f"✅ JSON: Có dữ liệu ({os.path.basename(data_file)})")
            else:
                st.info("📁 JSON: Chưa có dữ liệu")
        else:
            st.warning("⚠️ Chưa có stores nào")
            st.info("💡 Vào Store Manager để thêm store")
            if st.button("🏪 Mở Store Manager"):
                st.switch_page("pages/1_🏪_Store_Manager.py")
            return
        
        st.markdown("---")
        
        # Cấu hình Google Sheets
        st.subheader("📊 Google Sheets Integration")
        st.info("💡 Kết nối tự động với Google Sheets để sync dữ liệu")
        
        with st.expander("🔗 Cấu hình Google Sheets"):
            st.markdown("""
            **Quy trình tự động (khuyến nghị SyncWith):**
            1. **Google Ads** → Đồng bộ sang **Google Sheets** bằng công cụ như **SyncWith** (khuyến nghị) hoặc lịch export/connector bất kỳ.
            2. **Tool** → Tự động đọc từ Google Sheets và tự lưu **JSON backup**.

            **Checklist bắt buộc:**
            - Chia sẻ Google Sheet cho email của Service Account.
            - Hàng đầu là tiêu đề cột.
            - Nên có các cột: `date`, `campaign`, `impressions`, `clicks`, `cost`, `conversions`, `conversion_value`.
            - Bật lịch đồng bộ định kỳ trong SyncWith để dữ liệu luôn mới.
            """)
            
            # Form cấu hình Google Sheets
            with st.form("google_sheets_config"):
                st.markdown("**📋 Cấu hình Google Sheets:**")
                
                # Upload Google Sheets credentials
                sheets_credentials = st.file_uploader(
                    "📁 Google Sheets Credentials (JSON)",
                    type=['json'],
                    key="sheets_credentials"
                )
                
                spreadsheet_id = st.text_input(
                    "🆔 Spreadsheet ID",
                    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                    help="Lấy từ URL Google Sheets: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit"
                )
                
                sheet_name = st.text_input(
                    "📄 Sheet Name",
                    value="Sheet1",
                    help="Tên sheet chứa dữ liệu"
                )
                
                if st.form_submit_button("💾 Lưu cấu hình Google Sheets"):
                    if sheets_credentials and spreadsheet_id and sheet_name:
                        try:
                            credentials_content = sheets_credentials.getvalue().decode('utf-8')
                            
                            if save_google_sheets_config(selected_store_name, credentials_content, spreadsheet_id, sheet_name):
                                st.success("✅ Đã lưu cấu hình Google Sheets!")
                                st.info("🔄 Tool sẽ tự động sync dữ liệu từ Google Sheets")
                            else:
                                st.error("❌ Lỗi lưu cấu hình")
                        except Exception as e:
                            st.error(f"❌ Lỗi xử lý credentials: {e}")
                    else:
                        st.error("❌ Vui lòng điền đầy đủ thông tin")
        
        # Upload file dữ liệu (fallback)
        st.markdown("---")
        st.subheader("📁 Upload dữ liệu (Fallback)")
        st.info("💡 Upload file JSON nếu không dùng Google Sheets")
        
        uploaded_file = st.file_uploader(
            "Chọn file JSON",
            type=['json'],
            key="ads_upload"
        )
        
        if uploaded_file is not None:
            try:
                # Đọc dữ liệu từ file upload
                data = json.load(uploaded_file)
                
                # Lưu vào data directory
                data_file = get_ads_data_file(selected_store_name)
                os.makedirs(os.path.dirname(data_file), exist_ok=True)
                
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                st.success(f"✅ Đã lưu dữ liệu vào: {data_file}")
                
            except Exception as e:
                st.error(f"❌ Lỗi xử lý file: {e}")
        
        # Tạo dữ liệu demo
        st.markdown("---")
        st.subheader("🧪 Demo Data")
        if st.button("🎲 Tạo dữ liệu demo"):
            demo_data = create_demo_ads_data()
            data_file = get_ads_data_file(selected_store_name)
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(demo_data, f, indent=2, ensure_ascii=False)
            
            st.success("✅ Đã tạo dữ liệu demo!")
            st.rerun()
    
    # Main content
    if 'selected_store' in locals():
        st.header(f"📊 Phân tích Google Ads - {selected_store_name}")
        
        # Load dữ liệu
        df = load_ads_data(selected_store_name)
        
        if not df.empty:
            # Hiển thị thống kê tổng quan
            metrics = analyze_ads_performance(df)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("👁️ Impressions", f"{metrics['total_impressions']:,}")
                st.metric("🖱️ Clicks", f"{metrics['total_clicks']:,}")
            
            with col2:
                st.metric("💰 Cost", f"${metrics['total_cost']:,.2f}")
                st.metric("📊 CTR", f"{metrics['ctr']:.2f}%")
            
            with col3:
                st.metric("🎯 Conversions", f"{metrics['total_conversions']:,}")
                st.metric("💵 CPC", f"${metrics['cpc']:.2f}")
            
            with col4:
                st.metric("💎 ROAS", f"{metrics['roas']:.2f}x")
                st.metric("📈 Conv. Rate", f"{metrics['conversion_rate']:.2f}%")
            
            # Biểu đồ performance theo thời gian
            st.subheader("📈 Performance theo thời gian")
            
            if 'date' in df.columns:
                # Convert date column
                df['date'] = pd.to_datetime(df['date'])
                
                # Group by date
                daily_data = df.groupby('date').agg({
                    'impressions': 'sum',
                    'clicks': 'sum',
                    'cost': 'sum',
                    'conversions': 'sum',
                    'conversion_value': 'sum'
                }).reset_index()
                
                # Tính CTR và CPC
                daily_data['CTR'] = (daily_data['clicks'] / daily_data['impressions'] * 100).fillna(0)
                daily_data['CPC'] = (daily_data['cost'] / daily_data['clicks']).fillna(0)
                
                # Biểu đồ line chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=daily_data['date'],
                    y=daily_data['impressions'],
                    name='Impressions',
                    yaxis='y'
                ))
                
                fig.add_trace(go.Scatter(
                    x=daily_data['date'],
                    y=daily_data['clicks'],
                    name='Clicks',
                    yaxis='y'
                ))
                
                fig.add_trace(go.Scatter(
                    x=daily_data['date'],
                    y=daily_data['cost'],
                    name='Cost',
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title="Performance theo ngày",
                    xaxis_title="Ngày",
                    yaxis_title="Impressions/Clicks",
                    yaxis2=dict(title="Cost ($)", overlaying="y", side="right"),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Top campaigns
            st.subheader("🏆 Top Campaigns")
            
            if 'campaign' in df.columns:
                campaign_stats = df.groupby('campaign').agg({
                    'impressions': 'sum',
                    'clicks': 'sum',
                    'cost': 'sum',
                    'conversions': 'sum',
                    'conversion_value': 'sum'
                }).reset_index()
                
                campaign_stats['CTR'] = (campaign_stats['clicks'] / campaign_stats['impressions'] * 100).fillna(0)
                campaign_stats['CPC'] = (campaign_stats['cost'] / campaign_stats['clicks']).fillna(0)
                campaign_stats['ROAS'] = (campaign_stats['conversion_value'] / campaign_stats['cost']).fillna(0)
                
                # Top 10 campaigns by cost
                top_campaigns = campaign_stats.nlargest(10, 'cost')
                
                # Hiển thị bảng
                display_df = top_campaigns[['campaign', 'impressions', 'clicks', 'cost', 'CTR', 'CPC', 'ROAS']].copy()
                display_df.columns = ['Campaign', 'Impressions', 'Clicks', 'Cost ($)', 'CTR (%)', 'CPC ($)', 'ROAS']
                display_df['Cost ($)'] = display_df['Cost ($)'].round(2)
                display_df['CTR (%)'] = display_df['CTR (%)'].round(2)
                display_df['CPC ($)'] = display_df['CPC ($)'].round(2)
                display_df['ROAS'] = display_df['ROAS'].round(2)
                
                st.dataframe(display_df, use_container_width=True)
                
                # Biểu đồ top campaigns
                fig = px.bar(
                    top_campaigns,
                    x='campaign',
                    y='cost',
                    title="Top Campaigns by Cost",
                    labels={'campaign': 'Campaign', 'cost': 'Cost ($)'}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Raw data
            with st.expander("📋 Xem dữ liệu gốc"):
                st.dataframe(df, use_container_width=True)
                
                # Export options
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        file_name=f"google_ads_{selected_store_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    json_str = df.to_json(orient='records', indent=2)
                    st.download_button(
                        "📥 Download JSON",
                        json_str,
                        file_name=f"google_ads_{selected_store_name}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
        
        else:
            st.info("💡 Chưa có dữ liệu Google Ads")
            st.markdown("""
            **Hướng dẫn lấy dữ liệu (khuyến nghị SyncWith):**
            1. Dùng **SyncWith** để đồng bộ Google Ads → **Google Sheets** và chia sẻ sheet cho Service Account
            2. Vào mục **📊 Google Sheets Integration** (sidebar) để nhập `Spreadsheet ID` + `Sheet Name`
            3. Tool sẽ tự đọc và lưu **JSON backup** tự động

            **Fallback:** Upload file **JSON** ở sidebar hoặc dùng nút **🎲 Tạo dữ liệu demo**
            """)

if __name__ == "__main__":
    main()
