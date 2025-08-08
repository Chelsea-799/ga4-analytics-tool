#!/usr/bin/env python3
"""
Google Ads Analyzer - Tool phân tích dữ liệu Google Ads
"""

import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tempfile
import yaml

# Page config
st.set_page_config(
    page_title="Google Ads Analyzer",
    page_icon="📢",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_stores():
    """Tải danh sách stores từ file"""
    if os.path.exists('stores_data.json'):
        try:
            with open('stores_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def create_google_ads_yaml(store_data):
    """Tạo file google-ads.yaml tạm thời"""
    try:
        yaml_content = {
            'developer_token': store_data['google_ads_developer_token'],
            'client_id': store_data['google_ads_client_id'],
            'client_secret': store_data['google_ads_client_secret'],
            'refresh_token': store_data['google_ads_refresh_token'],
            'use_proto_plus': True
        }
        
        # Tạo file tạm thời
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml', mode='w') as tmp_file:
            yaml.dump(yaml_content, tmp_file, default_flow_style=False)
            return tmp_file.name
    except Exception as e:
        st.error(f"❌ Lỗi tạo file google-ads.yaml: {e}")
        return None

def fetch_google_ads_data(store_data, days=30):
    """Lấy dữ liệu từ Google Ads API"""
    try:
        # Tạo file google-ads.yaml
        yaml_path = create_google_ads_yaml(store_data)
        if not yaml_path:
            return None
        
        # Import Google Ads API
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        
        # Khởi tạo client
        client = GoogleAdsClient.load_from_storage(yaml_path)
        
        # Lấy customer service
        customer_service = client.get_service("CustomerService")
        
        # Lấy campaign service
        campaign_service = client.get_service("CampaignService")
        
        # Query campaigns
        query = """
            SELECT 
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.average_cpc,
                metrics.ctr,
                metrics.average_cpm
            FROM campaign 
            WHERE segments.date DURING LAST_30_DAYS
        """
        
        # Thực hiện query
        ga_service = client.get_service("GoogleAdsService")
        response = ga_service.search(
            customer_id=store_data['google_ads_customer_id'],
            query=query
        )
        
        # Parse kết quả
        data = []
        for row in response:
            data.append({
                'campaign_id': row.campaign.id,
                'campaign_name': row.campaign.name,
                'status': row.campaign.status.name,
                'channel_type': row.campaign.advertising_channel_type.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'cost_micros': row.metrics.cost_micros,
                'average_cpc': row.metrics.average_cpc,
                'ctr': row.metrics.ctr,
                'average_cpm': row.metrics.average_cpm
            })
        
        # Xóa file tạm thời
        os.unlink(yaml_path)
        
        return pd.DataFrame(data)
        
    except GoogleAdsException as ex:
        st.error(f"❌ Lỗi Google Ads API: {ex}")
        return None
    except Exception as e:
        st.error(f"❌ Lỗi khi lấy dữ liệu Google Ads: {e}")
        return None

def create_demo_ads_data():
    """Tạo dữ liệu demo cho Google Ads"""
    campaigns = [
        "Brand Campaign",
        "Product Search",
        "Retargeting",
        "Display Network",
        "Shopping Campaign"
    ]
    
    data = []
    for i, campaign in enumerate(campaigns):
        data.append({
            'campaign_id': f"campaign_{i+1}",
            'campaign_name': campaign,
            'status': 'ENABLED',
            'channel_type': 'SEARCH',
            'impressions': 10000 + i * 2000,
            'clicks': 500 + i * 100,
            'cost_micros': 5000000 + i * 1000000,  # 5 USD + i USD
            'average_cpc': 1000000 + i * 50000,  # 1 USD + i * 0.05 USD
            'ctr': 0.05 + i * 0.01,
            'average_cpm': 500000 + i * 50000  # 0.5 USD + i * 0.05 USD
        })
    
    return pd.DataFrame(data)

def analyze_ads_performance(df):
    """Phân tích hiệu suất Google Ads"""
    if df.empty:
        return {}
    
    # Tính toán metrics
    total_impressions = df['impressions'].sum()
    total_clicks = df['clicks'].sum()
    total_cost = df['cost_micros'].sum() / 1000000  # Convert to USD
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    avg_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
    avg_cpm = (total_cost / total_impressions * 1000) if total_impressions > 0 else 0
    
    # Top performing campaigns
    top_campaigns = df.nlargest(5, 'clicks')[['campaign_name', 'clicks', 'impressions', 'ctr']]
    
    # Cost analysis
    cost_analysis = df.nlargest(5, 'cost_micros')[['campaign_name', 'cost_micros', 'clicks', 'average_cpc']]
    
    return {
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'total_cost': total_cost,
        'avg_ctr': avg_ctr,
        'avg_cpc': avg_cpc,
        'avg_cpm': avg_cpm,
        'top_campaigns': top_campaigns,
        'cost_analysis': cost_analysis
    }

def main():
    """Hàm chính"""
    st.title("📢 Google Ads Analyzer")
    st.markdown("Phân tích dữ liệu Google Ads với AI")
    st.markdown("---")
    
    # Load stores
    stores = load_stores()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        
        # Chọn store
        store_names = list(stores.keys())
        if not store_names:
            st.warning("📝 Chưa có store nào. Hãy vào Store Manager để thêm store!")
            return
        
        selected_store = st.selectbox(
            "🏪 Chọn Store",
            store_names,
            index=0
        )
        
        if selected_store:
            store_data = stores[selected_store]
            
            # Kiểm tra Google Ads config
            if not store_data.get('google_ads_customer_id'):
                st.error("❌ Store này chưa cấu hình Google Ads!")
                st.info("💡 Vào Store Manager để cấu hình Google Ads")
                return
            
            st.success("✅ Google Ads đã cấu hình")
            
            # Date range
            st.subheader("📅 Thời gian phân tích")
            days = st.slider("Số ngày", 7, 90, 30)
            
            # OpenAI API Key
            st.subheader("🤖 OpenAI API")
            openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
            
            # Analyze button
            if st.button("🚀 Phân tích Google Ads", use_container_width=True):
                st.session_state['analyze_ads'] = True
                st.session_state['selected_store'] = store_data
                st.session_state['days'] = days
                st.session_state['openai_key'] = openai_key
    
    # Main content
    if 'analyze_ads' in st.session_state and st.session_state['analyze_ads']:
        store_data = st.session_state['selected_store']
        days = st.session_state['days']
        
        with st.spinner("🔄 Đang lấy dữ liệu Google Ads..."):
            # Lấy dữ liệu
            df = fetch_google_ads_data(store_data, days)
            
            if df is None or df.empty:
                st.warning("⚠️ Không thể lấy dữ liệu từ Google Ads API. Hiển thị dữ liệu demo...")
                df = create_demo_ads_data()
            
            # Phân tích hiệu suất
            performance = analyze_ads_performance(df)
            
            # Hiển thị kết quả
            st.success("✅ Đã lấy dữ liệu Google Ads thành công!")
            
            # Metrics overview
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👁️ Impressions", f"{performance['total_impressions']:,}")
            with col2:
                st.metric("🖱️ Clicks", f"{performance['total_clicks']:,}")
            with col3:
                st.metric("💰 Cost", f"${performance['total_cost']:,.2f}")
            with col4:
                st.metric("📊 CTR", f"{performance['avg_ctr']:.2f}%")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Top Campaigns by Clicks")
                fig = px.bar(
                    performance['top_campaigns'],
                    x='campaign_name',
                    y='clicks',
                    title="Top 5 Campaigns by Clicks"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("💰 Cost Analysis")
                cost_df = performance['cost_analysis'].copy()
                cost_df['cost_usd'] = cost_df['cost_micros'] / 1000000
                
                fig = px.bar(
                    cost_df,
                    x='campaign_name',
                    y='cost_usd',
                    title="Top 5 Campaigns by Cost"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.subheader("📋 Chi tiết Campaigns")
            display_df = df.copy()
            display_df['cost_usd'] = display_df['cost_micros'] / 1000000
            display_df['ctr_percent'] = display_df['ctr'] * 100
            display_df['cpc_usd'] = display_df['average_cpc'] / 1000000
            display_df['cpm_usd'] = display_df['average_cpm'] / 1000000
            
            # Rename columns
            display_df = display_df[[
                'campaign_name', 'status', 'impressions', 'clicks', 
                'cost_usd', 'ctr_percent', 'cpc_usd', 'cpm_usd'
            ]]
            display_df.columns = [
                'Campaign Name', 'Status', 'Impressions', 'Clicks',
                'Cost (USD)', 'CTR (%)', 'CPC (USD)', 'CPM (USD)'
            ]
            
            st.dataframe(display_df, use_container_width=True)
            
            # AI Insights
            if st.session_state.get('openai_key'):
                st.subheader("🤖 Phân tích AI")
                if st.button("💡 Tạo insights"):
                    # TODO: Implement AI insights
                    st.info("🚧 Tính năng AI insights đang phát triển...")
    
    else:
        # Instructions
        st.info("💡 Chọn store và cấu hình ở sidebar, sau đó nhấn 'Phân tích Google Ads'")

if __name__ == "__main__":
    main()
