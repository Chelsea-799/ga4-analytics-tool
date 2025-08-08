#!/usr/bin/env python3
"""
GA4 + Google Ads Analyzer - Tool phân tích kết hợp dữ liệu GA4 và Google Ads
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
    page_title="GA4 + Google Ads Analyzer",
    page_icon="📊",
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

def fetch_ga4_data(store_data, days=30):
    """Lấy dữ liệu GA4"""
    try:
        # Import GA4 API
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Metric, Dimension
        )
        
        # Tạo file credentials tạm thời
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as tmp_file:
            tmp_file.write(store_data['ga4_credentials_content'])
            credentials_path = tmp_file.name
        
        # Khởi tạo client
        client = BetaAnalyticsDataClient.from_service_account_file(credentials_path)
        
        # Query GA4 data
        request = RunReportRequest(
            property=f"properties/{store_data['ga4_property_id']}",
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
        
        # Parse data
        data = []
        for row in response.rows:
            data.append({
                'date': row.dimension_values[0].value,
                'totalUsers': int(row.metric_values[0].value),
                'sessions': int(row.metric_values[1].value),
                'screenPageViews': int(row.metric_values[2].value),
                'transactions': int(row.metric_values[3].value),
                'totalRevenue': float(row.metric_values[4].value)
            })
        
        # Xóa file tạm thời
        os.unlink(credentials_path)
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"❌ Lỗi khi lấy dữ liệu GA4: {e}")
        return None

def fetch_google_ads_data(store_data, days=30):
    """Lấy dữ liệu Google Ads"""
    try:
        # Tạo file google-ads.yaml
        yaml_content = {
            'developer_token': store_data['google_ads_developer_token'],
            'client_id': store_data['google_ads_client_id'],
            'client_secret': store_data['google_ads_client_secret'],
            'refresh_token': store_data['google_ads_refresh_token'],
            'use_proto_plus': True
        }
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml', mode='w') as tmp_file:
            yaml.dump(yaml_content, tmp_file, default_flow_style=False)
            yaml_path = tmp_file.name
        
        # Import Google Ads API
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        
        # Khởi tạo client
        client = GoogleAdsClient.load_from_storage(yaml_path)
        
        # Query campaigns
        query = """
            SELECT 
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.average_cpc,
                metrics.ctr
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
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'cost_micros': row.metrics.cost_micros,
                'average_cpc': row.metrics.average_cpc,
                'ctr': row.metrics.ctr
            })
        
        # Xóa file tạm thời
        os.unlink(yaml_path)
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"❌ Lỗi khi lấy dữ liệu Google Ads: {e}")
        return None

def create_demo_data():
    """Tạo dữ liệu demo"""
    # GA4 demo data
    ga4_data = []
    for i in range(30):
        date = (datetime.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        ga4_data.append({
            'date': date,
            'totalUsers': 1000 + i * 50,
            'sessions': 1500 + i * 75,
            'screenPageViews': 3000 + i * 150,
            'transactions': 50 + i * 3,
            'totalRevenue': 5000 + i * 250
        })
    
    # Google Ads demo data
    ads_data = []
    campaigns = ["Brand Campaign", "Product Search", "Retargeting", "Display Network"]
    for i, campaign in enumerate(campaigns):
        ads_data.append({
            'campaign_id': f"campaign_{i+1}",
            'campaign_name': campaign,
            'status': 'ENABLED',
            'impressions': 10000 + i * 2000,
            'clicks': 500 + i * 100,
            'cost_micros': 5000000 + i * 1000000,
            'average_cpc': 1000000 + i * 50000,
            'ctr': 0.05 + i * 0.01
        })
    
    return pd.DataFrame(ga4_data), pd.DataFrame(ads_data)

def analyze_combined_data(ga4_df, ads_df):
    """Phân tích dữ liệu kết hợp"""
    analysis = {}
    
    # GA4 Analysis
    if not ga4_df.empty:
        analysis['ga4'] = {
            'total_users': ga4_df['totalUsers'].sum(),
            'total_sessions': ga4_df['sessions'].sum(),
            'total_pageviews': ga4_df['screenPageViews'].sum(),
            'total_transactions': ga4_df['transactions'].sum(),
            'total_revenue': ga4_df['totalRevenue'].sum(),
            'avg_session_duration': ga4_df['screenPageViews'].sum() / ga4_df['sessions'].sum() if ga4_df['sessions'].sum() > 0 else 0,
            'conversion_rate': (ga4_df['transactions'].sum() / ga4_df['sessions'].sum() * 100) if ga4_df['sessions'].sum() > 0 else 0
        }
    
    # Google Ads Analysis
    if not ads_df.empty:
        analysis['ads'] = {
            'total_impressions': ads_df['impressions'].sum(),
            'total_clicks': ads_df['clicks'].sum(),
            'total_cost': ads_df['cost_micros'].sum() / 1000000,
            'avg_ctr': (ads_df['clicks'].sum() / ads_df['impressions'].sum() * 100) if ads_df['impressions'].sum() > 0 else 0,
            'avg_cpc': (ads_df['cost_micros'].sum() / ads_df['clicks'].sum() / 1000000) if ads_df['clicks'].sum() > 0 else 0
        }
    
    # Combined Analysis
    if not ga4_df.empty and not ads_df.empty:
        analysis['combined'] = {
            'roas': analysis['ga4']['total_revenue'] / analysis['ads']['total_cost'] if analysis['ads']['total_cost'] > 0 else 0,
            'cost_per_conversion': analysis['ads']['total_cost'] / analysis['ga4']['total_transactions'] if analysis['ga4']['total_transactions'] > 0 else 0,
            'conversion_rate_from_ads': (analysis['ga4']['total_transactions'] / analysis['ads']['total_clicks'] * 100) if analysis['ads']['total_clicks'] > 0 else 0
        }
    
    return analysis

def main():
    """Hàm chính"""
    st.title("📊 GA4 + Google Ads Analyzer")
    st.markdown("Phân tích toàn diện dữ liệu GA4 và Google Ads")
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
            
            # Kiểm tra config
            ga4_configured = store_data.get('ga4_property_id') and store_data.get('ga4_credentials_content')
            ads_configured = store_data.get('google_ads_customer_id') and store_data.get('google_ads_developer_token')
            
            if not ga4_configured and not ads_configured:
                st.error("❌ Store này chưa cấu hình GA4 hoặc Google Ads!")
                st.info("💡 Vào Store Manager để cấu hình")
                return
            
            if ga4_configured:
                st.success("✅ GA4 đã cấu hình")
            else:
                st.warning("⚠️ GA4 chưa cấu hình")
            
            if ads_configured:
                st.success("✅ Google Ads đã cấu hình")
            else:
                st.warning("⚠️ Google Ads chưa cấu hình")
            
            # Date range
            st.subheader("📅 Thời gian phân tích")
            days = st.slider("Số ngày", 7, 90, 30)
            
            # OpenAI API Key
            st.subheader("🤖 OpenAI API")
            openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
            
            # Analyze button
            if st.button("🚀 Phân tích kết hợp", use_container_width=True):
                st.session_state['analyze_combined'] = True
                st.session_state['selected_store'] = store_data
                st.session_state['days'] = days
                st.session_state['openai_key'] = openai_key
    
    # Main content
    if 'analyze_combined' in st.session_state and st.session_state['analyze_combined']:
        store_data = st.session_state['selected_store']
        days = st.session_state['days']
        
        with st.spinner("🔄 Đang lấy dữ liệu GA4 và Google Ads..."):
            # Lấy dữ liệu GA4
            ga4_df = None
            if store_data.get('ga4_property_id'):
                ga4_df = fetch_ga4_data(store_data, days)
            
            # Lấy dữ liệu Google Ads
            ads_df = None
            if store_data.get('google_ads_customer_id'):
                ads_df = fetch_google_ads_data(store_data, days)
            
            # Fallback to demo data
            if ga4_df is None and ads_df is None:
                st.warning("⚠️ Không thể lấy dữ liệu từ APIs. Hiển thị dữ liệu demo...")
                ga4_df, ads_df = create_demo_data()
            elif ga4_df is None:
                st.warning("⚠️ Không thể lấy dữ liệu GA4. Sử dụng dữ liệu demo...")
                ga4_df, _ = create_demo_data()
            elif ads_df is None:
                st.warning("⚠️ Không thể lấy dữ liệu Google Ads. Sử dụng dữ liệu demo...")
                _, ads_df = create_demo_data()
            
            # Phân tích dữ liệu
            analysis = analyze_combined_data(ga4_df, ads_df)
            
            # Hiển thị kết quả
            st.success("✅ Đã lấy dữ liệu thành công!")
            
            # Combined Metrics
            st.subheader("📊 Tổng quan hiệu suất")
            
            if 'ga4' in analysis and 'ads' in analysis:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("👥 Users", f"{analysis['ga4']['total_users']:,}")
                    st.metric("👁️ Impressions", f"{analysis['ads']['total_impressions']:,}")
                
                with col2:
                    st.metric("🖱️ Clicks", f"{analysis['ads']['total_clicks']:,}")
                    st.metric("📊 Sessions", f"{analysis['ga4']['total_sessions']:,}")
                
                with col3:
                    st.metric("💰 Revenue", f"${analysis['ga4']['total_revenue']:,.2f}")
                    st.metric("💸 Cost", f"${analysis['ads']['total_cost']:,.2f}")
                
                with col4:
                    st.metric("📈 ROAS", f"{analysis['combined']['roas']:.2f}x")
                    st.metric("🎯 Conv. Rate", f"{analysis['ga4']['conversion_rate']:.2f}%")
            
            # Charts
            st.subheader("📈 Biểu đồ phân tích")
            
            if not ga4_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # GA4 Trends
                    fig = px.line(ga4_df, x='date', y=['totalUsers', 'sessions'], 
                                title="GA4 Trends - Users & Sessions")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Revenue vs Cost
                    if not ads_df.empty:
                        revenue_data = ga4_df[['date', 'totalRevenue']].copy()
                        revenue_data['totalCost'] = analysis['ads']['total_cost'] / len(ga4_df)
                        
                        fig = px.line(revenue_data, x='date', y=['totalRevenue', 'totalCost'],
                                    title="Revenue vs Cost Trend")
                        st.plotly_chart(fig, use_container_width=True)
            
            # Campaign Performance
            if not ads_df.empty:
                st.subheader("📢 Campaign Performance")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Top campaigns by clicks
                    top_campaigns = ads_df.nlargest(5, 'clicks')[['campaign_name', 'clicks', 'impressions']]
                    fig = px.bar(top_campaigns, x='campaign_name', y='clicks',
                               title="Top Campaigns by Clicks")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Cost analysis
                    cost_df = ads_df.nlargest(5, 'cost_micros').copy()
                    cost_df['cost_usd'] = cost_df['cost_micros'] / 1000000
                    
                    fig = px.bar(cost_df, x='campaign_name', y='cost_usd',
                               title="Top Campaigns by Cost")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Detailed Tables
            st.subheader("📋 Chi tiết dữ liệu")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not ga4_df.empty:
                    st.write("**GA4 Data:**")
                    display_ga4 = ga4_df.copy()
                    display_ga4['totalRevenue'] = display_ga4['totalRevenue'].round(2)
                    st.dataframe(display_ga4, use_container_width=True)
            
            with col2:
                if not ads_df.empty:
                    st.write("**Google Ads Data:**")
                    display_ads = ads_df.copy()
                    display_ads['cost_usd'] = display_ads['cost_micros'] / 1000000
                    display_ads['ctr_percent'] = display_ads['ctr'] * 100
                    display_ads = display_ads[['campaign_name', 'impressions', 'clicks', 'cost_usd', 'ctr_percent']]
                    display_ads.columns = ['Campaign', 'Impressions', 'Clicks', 'Cost (USD)', 'CTR (%)']
                    st.dataframe(display_ads, use_container_width=True)
            
            # AI Insights
            if st.session_state.get('openai_key'):
                st.subheader("🤖 Phân tích AI")
                if st.button("💡 Tạo insights"):
                    # TODO: Implement AI insights
                    st.info("🚧 Tính năng AI insights đang phát triển...")
    
    else:
        # Instructions
        st.info("💡 Chọn store và cấu hình ở sidebar, sau đó nhấn 'Phân tích kết hợp'")

if __name__ == "__main__":
    main()
