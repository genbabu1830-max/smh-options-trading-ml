#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit App for Testing Recommendation Agent
Interactive UI for generating and testing options trade recommendations
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import json
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.recommendation_agent import RecommendationAgent

# Page config
st.set_page_config(
    page_title="Options Trading Agent",
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'recommendation' not in st.session_state:
    st.session_state.recommendation = None
if 'history' not in st.session_state:
    st.session_state.history = []

# Header
st.markdown('<div class="main-header">📊 Options Trading Recommendation Agent</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Ticker selection
    ticker = st.selectbox(
        "Select Ticker",
        options=["SMH", "SPY", "QQQ", "IWM"],
        index=0,
        help="Select the ETF to analyze"
    )
    
    # Date selection
    st.subheader("📅 Date Selection")
    use_current_date = st.checkbox("Use Current Date", value=True)
    
    if use_current_date:
        selected_date = datetime.now().strftime('%Y-%m-%d')
        st.info(f"Using current date: {selected_date}")
    else:
        date_input = st.date_input(
            "Select Date",
            value=datetime.now(),
            min_value=datetime(2024, 1, 1),
            max_value=datetime.now(),
            help="Select a historical date for backtesting"
        )
        selected_date = date_input.strftime('%Y-%m-%d')
    
    # Model source
    st.subheader("🗄️ Model Source")
    use_s3 = st.radio(
        "Load models from:",
        options=[False, True],
        format_func=lambda x: "Local Storage" if not x else "S3 Bucket",
        index=0,
        help="Local: Fast, for testing. S3: Production mode"
    )
    
    # Initialize agent button
    st.markdown("---")
    if st.button("🚀 Initialize Agent", type="primary", use_container_width=True):
        with st.spinner("Initializing agent..."):
            try:
                st.session_state.agent = RecommendationAgent(
                    ticker=ticker,
                    use_s3=use_s3
                )
                st.success("✅ Agent initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize agent: {e}")
    
    # Agent status
    if st.session_state.agent:
        st.success("✅ Agent Ready")
        st.info(f"Ticker: {ticker}")
        st.info(f"Model: {'S3' if use_s3 else 'Local'}")
    else:
        st.warning("⚠️ Agent not initialized")
    
    # Clear history
    st.markdown("---")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.history = []
        st.session_state.recommendation = None
        st.rerun()

# Main content
if st.session_state.agent is None:
    st.info("👈 Please initialize the agent using the sidebar configuration")
    
    # Show example
    with st.expander("📖 How to Use"):
        st.markdown("""
        ### Getting Started
        
        1. **Select Ticker**: Choose the ETF you want to analyze (SMH, SPY, QQQ, IWM)
        2. **Choose Date**: Use current date or select a historical date for backtesting
        3. **Select Model Source**: Local (fast) or S3 (production)
        4. **Initialize Agent**: Click the "Initialize Agent" button
        5. **Generate Recommendation**: Click "Generate Recommendation" to get trade suggestions
        
        ### Features
        
        - **Two-Stage System**: ML predicts strategy (84.21% accuracy) + Rules generate parameters
        - **10 Strategies**: Iron Condor, Long Call/Put, Spreads, Straddles, etc.
        - **Risk Validation**: Automatic position sizing and risk checks
        - **Historical Testing**: Test on any past date for backtesting
        - **Recommendation History**: Track all generated recommendations
        
        ### Strategy Types
        
        - **Iron Condor**: High IV + Ranging market
        - **Iron Butterfly**: Very high IV + Tight range
        - **Long Call/Put**: Low IV + Strong trend
        - **Bull/Bear Spreads**: Medium IV + Moderate trend
        - **Straddles/Strangles**: Low IV + Uncertain direction
        - **Calendar/Diagonal**: Specific market conditions
        """)

else:
    # Generate recommendation section
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"📈 Generate Recommendation for {ticker}")
    
    with col2:
        st.metric("Date", selected_date)
    
    with col3:
        if st.button("🎯 Generate Recommendation", type="primary", use_container_width=True):
            with st.spinner("Generating recommendation..."):
                try:
                    recommendation = st.session_state.agent.generate_recommendation(date=selected_date)
                    st.session_state.recommendation = recommendation
                    
                    # Add to history
                    st.session_state.history.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'ticker': ticker,
                        'date': selected_date,
                        'strategy': recommendation['strategy']['strategy'],
                        'confidence': recommendation['strategy']['confidence']
                    })
                    
                    st.success("✅ Recommendation generated!")
                except Exception as e:
                    st.error(f"❌ Failed to generate recommendation: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Display recommendation
    if st.session_state.recommendation:
        rec = st.session_state.recommendation
        
        st.markdown("---")
        
        # Strategy Overview
        st.subheader("🎯 Recommended Strategy")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Strategy",
                rec['strategy']['strategy'].replace('_', ' ').title(),
                help="ML model prediction"
            )
        
        with col2:
            confidence = rec['strategy']['confidence']
            st.metric(
                "Confidence",
                f"{confidence:.1%}",
                delta=f"{(confidence - 0.5) * 100:.1f}% vs 50%",
                help="Model confidence in this prediction"
            )
        
        with col3:
            st.metric(
                "Model Accuracy",
                f"{rec['strategy']['model_accuracy']:.1%}",
                help="Historical model accuracy"
            )
        
        with col4:
            st.metric(
                "Model Version",
                rec['strategy']['model_version'],
                help="ML model version"
            )
        
        # Alternative strategies
        if rec['strategy'].get('alternatives'):
            with st.expander("🔄 Alternative Strategies"):
                alt_df = pd.DataFrame(rec['strategy']['alternatives'])
                alt_df['confidence'] = alt_df['confidence'].apply(lambda x: f"{x:.1%}")
                alt_df.columns = ['Strategy', 'Confidence']
                st.dataframe(alt_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Trade Parameters
        st.subheader("💰 Trade Parameters")
        
        params = rec['parameters']
        strategy_name = rec['strategy']['strategy']
        
        # Display parameters based on strategy type
        if strategy_name == 'IRON_CONDOR':
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Put Spread**")
                st.write(f"Long Strike: ${params.get('put_long_strike', 0):.2f}")
                st.write(f"Short Strike: ${params.get('put_short_strike', 0):.2f}")
            
            with col2:
                st.markdown("**Call Spread**")
                st.write(f"Short Strike: ${params.get('call_short_strike', 0):.2f}")
                st.write(f"Long Strike: ${params.get('call_long_strike', 0):.2f}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("DTE", f"{params.get('dte', 0)} days")
            with col2:
                st.metric("Contracts", params.get('contracts', 0))
            with col3:
                st.metric("Net Credit", f"${params.get('total_credit', 0):.2f}")
            with col4:
                st.metric("Max Profit", f"${params.get('total_max_profit', 0):.2f}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Max Loss", f"${params.get('total_max_loss', 0):.2f}")
            with col2:
                st.metric("Risk/Reward", f"{params.get('risk_reward_ratio', 0):.2f}")
            with col3:
                profit_zone = f"${params.get('breakeven_down', 0):.2f} - ${params.get('breakeven_up', 0):.2f}"
                st.metric("Profit Zone", profit_zone)
        
        elif strategy_name in ['LONG_CALL', 'LONG_PUT']:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Strike", f"${params.get('strike', 0):.2f}")
            with col2:
                st.metric("DTE", f"{params.get('dte', 0)} days")
            with col3:
                st.metric("Contracts", params.get('contracts', 0))
            with col4:
                st.metric("Total Cost", f"${params.get('total_cost', 0):.2f}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Max Loss", f"${params.get('max_loss', 0):.2f}")
            with col2:
                st.metric("Breakeven", f"${params.get('breakeven', 0):.2f}")
        
        elif strategy_name in ['BULL_CALL_SPREAD', 'BEAR_PUT_SPREAD']:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Long Strike", f"${params.get('long_strike', 0):.2f}")
            with col2:
                st.metric("Short Strike", f"${params.get('short_strike', 0):.2f}")
            with col3:
                st.metric("DTE", f"{params.get('dte', 0)} days")
            with col4:
                st.metric("Contracts", params.get('contracts', 0))
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Net Debit", f"${params.get('total_debit', 0):.2f}")
            with col2:
                st.metric("Max Profit", f"${params.get('total_max_profit', 0):.2f}")
            with col3:
                st.metric("Max Loss", f"${params.get('total_max_loss', 0):.2f}")
            with col4:
                st.metric("Breakeven", f"${params.get('breakeven', 0):.2f}")
        
        st.markdown("---")
        
        # Market Conditions
        st.subheader("📈 Market Conditions")
        
        features = rec['features']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Current Price", f"${features.get('current_price', 0):.2f}")
        
        with col2:
            st.metric("IV Rank", f"{features.get('iv_rank', 0):.1f}%")
        
        with col3:
            trend_regime = features.get('trend_regime', 2)
            trend_names = ['Strong Down', 'Weak Down', 'Ranging', 'Weak Up', 'Strong Up']
            trend = trend_names[trend_regime] if 0 <= trend_regime < 5 else 'Unknown'
            st.metric("Trend", trend)
        
        with col4:
            st.metric("ADX", f"{features.get('adx_14', 0):.1f}")
        
        with col5:
            st.metric("RSI", f"{features.get('rsi_14', 0):.1f}")
        
        # Risk Validation
        if 'risk_validation' in params:
            st.markdown("---")
            st.subheader("✅ Risk Validation")
            
            validation = params['risk_validation']
            
            if validation.get('approved', False):
                st.markdown('<div class="success-box">✅ <strong>TRADE APPROVED</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-box">❌ <strong>TRADE REJECTED</strong></div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Risk/Reward Ratio", f"{validation.get('risk_reward_ratio', 0):.2f}")
            with col2:
                st.metric("Risk Percentage", f"{validation.get('risk_percentage', 0):.2%}")
            with col3:
                st.metric("Position Size", f"${validation.get('position_size', 0):.2f}")
        
        # Formatted Output
        with st.expander("📄 Formatted Recommendation"):
            st.code(rec['formatted_output'], language=None)
        
        # Raw Data
        with st.expander("🔍 Raw Data (JSON)"):
            st.json(rec)
        
        # Download button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            json_str = json.dumps(rec, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"recommendation_{ticker}_{selected_date}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                label="📥 Download Text",
                data=rec['formatted_output'],
                file_name=f"recommendation_{ticker}_{selected_date}.txt",
                mime="text/plain",
                use_container_width=True
            )

# History section
if st.session_state.history:
    st.markdown("---")
    st.subheader("📜 Recommendation History")
    
    history_df = pd.DataFrame(st.session_state.history)
    history_df['confidence'] = history_df['confidence'].apply(lambda x: f"{x:.1%}")
    
    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp": "Timestamp",
            "ticker": "Ticker",
            "date": "Date",
            "strategy": "Strategy",
            "confidence": "Confidence"
        }
    )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p><strong>Options Trading Recommendation Agent</strong></p>
    <p>Powered by Strands Agents Framework | ML Model Accuracy: 84.21%</p>
    <p>⚠️ For testing purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
