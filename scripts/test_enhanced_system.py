#!/usr/bin/env python3
"""
Enhanced System Test - Complete Two-Stage Workflow
==================================================

Tests the complete production system with enhanced parameter generation:
1. Feature Extraction (Stage 0)
2. Strategy Prediction (Stage 1 - ML)
3. Parameter Generation (Stage 2 - Enhanced Rules)

Features:
- IV-adaptive strike selection
- Delta-based targeting
- Trend-strength adjustments
- Risk management and position sizing
"""

import sys
import os
import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.feature_extractor import FeatureExtractor
from scripts.utils.parameter_generator import ParameterGenerator, RiskManager


def load_test_data(target_date=None):
    """Load option chain and price history for testing."""
    print("Loading test data...")
    
    # Load checkpoint file
    df = pd.read_csv('smh_historical_data/smh_checkpoint_500.csv')
    df['date'] = pd.to_datetime(df['window_start'], unit='ns').dt.strftime('%Y-%m-%d')
    
    # Get available dates
    available_dates = sorted(df['date'].unique())
    
    if target_date is None:
        target_date = available_dates[-1]
    
    print(f"  Selected date: {target_date}")
    
    # Filter for target date
    day_data = df[df['date'] == target_date].copy()
    
    # Create option chain
    volume_numeric = pd.to_numeric(day_data['volume'], errors='coerce').fillna(100).astype(int)
    oi_numeric = pd.to_numeric(day_data['open_interest'], errors='coerce').fillna(1000).astype(int)
    
    option_chain = pd.DataFrame({
        'strike': day_data['strike'],
        'type': day_data['type'],
        'expiration': day_data['expiration_date'],
        'dte': day_data['dte'],
        'bid': day_data['close'] * 0.98,
        'ask': day_data['close'] * 1.02,
        'volume': volume_numeric,
        'open_interest': oi_numeric,
        'iv': day_data['implied_volatility'],
        'delta': day_data['delta'],
        'gamma': day_data['gamma'],
        'theta': day_data['theta'],
        'vega': day_data['vega']
    })
    
    option_chain = option_chain.dropna(subset=['strike', 'type', 'iv', 'delta'])
    
    print(f"✓ Loaded {len(option_chain)} option contracts")
    
    # Create price history
    price_data = df.groupby('date').agg({
        'underlying': 'first',
        'volume': 'sum',
        'open': 'first',
        'high': 'first',
        'low': 'first',
        'close': 'first'
    }).reset_index()
    
    underlying_price = pd.to_numeric(price_data['underlying'], errors='coerce')
    if underlying_price.isna().all():
        underlying_price = pd.to_numeric(price_data['close'], errors='coerce')
    
    price_history = pd.DataFrame({
        'date': price_data['date'],
        'open': underlying_price,
        'high': underlying_price * 1.005,
        'low': underlying_price * 0.995,
        'close': underlying_price,
        'volume': 50000000
    })
    
    price_history = price_history.dropna(subset=['close']).sort_values('date').reset_index(drop=True)
    
    print(f"✓ Created {len(price_history)} days of price history")
    
    return option_chain, price_history, target_date


def main():
    print("=" * 70)
    print("ENHANCED SYSTEM TEST - TWO-STAGE WORKFLOW")
    print("=" * 70)
    print()
    
    # Load data
    print("=" * 70)
    print("STEP 1: LOAD DATA")
    print("=" * 70)
    option_chain, price_history, date = load_test_data()
    
    # Extract features (Stage 0)
    print("\n" + "=" * 70)
    print("STEP 2: EXTRACT FEATURES (STAGE 0)")
    print("=" * 70)
    
    extractor = FeatureExtractor()
    features = extractor.extract_features(
        option_chain=option_chain,
        price_history=price_history,
        current_date=date
    )
    
    print(f"✓ Extracted {len(features)} features")
    print(f"\nKey Market Conditions:")
    print(f"  Current Price: ${features['current_price']:.2f}")
    print(f"  IV Rank: {features['iv_rank']:.1f}%")
    print(f"  ADX: {features['adx_14']:.1f}")
    print(f"  RSI: {features['rsi_14']:.1f}")
    print(f"  Trend: {['Strong Down', 'Weak Down', 'Ranging', 'Weak Up', 'Strong Up'][features['trend_regime']]}")
    print(f"  Volatility: {['Very Low', 'Low', 'Normal', 'Elevated', 'Very High'][features['volatility_regime']]}")
    
    # Predict strategy (Stage 1)
    print("\n" + "=" * 70)
    print("STEP 3: PREDICT STRATEGY (STAGE 1 - ML MODEL)")
    print("=" * 70)
    
    try:
        import joblib
        model = joblib.load('models/lightgbm_clean_model.pkl')
        label_encoder = joblib.load('models/label_encoder_clean.pkl')
    except:
        with open('models/lightgbm_clean_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('models/label_encoder_clean.pkl', 'rb') as f:
            label_encoder = pickle.load(f)
    
    feature_df = extractor.get_feature_dataframe(features)
    prediction = model.predict(feature_df)[0]
    probabilities = model.predict_proba(feature_df)[0]
    
    strategy = label_encoder.inverse_transform([prediction])[0]
    confidence = probabilities[prediction]
    
    top_3_idx = np.argsort(probabilities)[-3:][::-1]
    top_3 = [(label_encoder.inverse_transform([idx])[0], probabilities[idx]) for idx in top_3_idx]
    
    print(f"\n🎯 PREDICTED STRATEGY: {strategy}")
    print(f"   Confidence: {confidence:.1%}")
    print(f"\n   Top 3 Strategies:")
    for i, (strat, conf) in enumerate(top_3, 1):
        print(f"   {i}. {strat}: {conf:.1%}")
    
    # Generate parameters (Stage 2 - Enhanced)
    print("\n" + "=" * 70)
    print("STEP 4: GENERATE PARAMETERS (STAGE 2 - ENHANCED RULES)")
    print("=" * 70)
    
    # Initialize risk manager
    risk_manager = RiskManager(
        account_size=10000,
        risk_per_trade=0.02,  # 2% max risk
        max_contracts=10
    )
    
    # Initialize parameter generator
    param_gen = ParameterGenerator(risk_manager=risk_manager)
    
    print(f"\nGenerating enhanced parameters for {strategy}...")
    print(f"  Account Size: ${risk_manager.account_size:,.0f}")
    print(f"  Max Risk per Trade: {risk_manager.risk_per_trade:.1%} (${risk_manager.max_risk_amount:.0f})")
    
    try:
        parameters = param_gen.generate(
            strategy=strategy,
            option_chain=option_chain,
            features=features,
            current_price=features['current_price']
        )
        
        print(f"\n✓ Generated parameters with enhanced logic")
        print(f"\n📋 TRADE PARAMETERS:")
        print(f"{'=' * 60}")
        
        for key, value in parameters.items():
            if isinstance(value, float):
                if 'cost' in key or 'profit' in key or 'loss' in key or 'credit' in key or 'debit' in key:
                    print(f"  {key:30s}: ${value:,.2f}")
                elif 'strike' in key or 'breakeven' in key:
                    print(f"  {key:30s}: ${value:.2f}")
                elif 'ratio' in key or 'delta' in key:
                    print(f"  {key:30s}: {value:.3f}")
                else:
                    print(f"  {key:30s}: {value:.2f}")
            else:
                print(f"  {key:30s}: {value}")
        
        # Validate trade
        if 'max_loss' in parameters and 'max_profit' in parameters:
            max_loss = parameters.get('total_max_loss', parameters.get('max_loss', 0))
            max_profit = parameters.get('total_max_profit', parameters.get('max_profit', 0))
            
            if isinstance(max_profit, str):
                max_profit = max_loss * 3  # Estimate for unlimited profit strategies
            
            validation = risk_manager.validate_trade(max_loss, max_profit)
            
            print(f"\n🔍 RISK VALIDATION:")
            print(f"{'=' * 60}")
            print(f"  Status: {'✅ APPROVED' if validation['approved'] else '❌ REJECTED'}")
            print(f"  Risk/Reward Ratio: {validation['risk_reward_ratio']:.2f}")
            print(f"  Risk Percentage: {validation['risk_percentage']:.2%}")
            print(f"  Max Risk Amount: ${validation['max_risk_amount']:.2f}")
            
            if not validation['approved']:
                print(f"\n  ⚠️ Trade exceeds risk limits!")
        
        # Show execution instructions
        print(f"\n📝 EXECUTION INSTRUCTIONS:")
        print(f"{'=' * 60}")
        
        if strategy == 'LONG_CALL':
            print(f"1. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['strike']:.0f} CALL")
            print(f"   Expiration: {parameters['dte']} days")
            print(f"   Cost: ${parameters['total_cost']:.2f}")
            print(f"2. Set stop loss at 50% of premium paid")
            print(f"3. Target: Price moves above ${parameters['breakeven']:.2f}")
        
        elif strategy == 'LONG_PUT':
            print(f"1. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['strike']:.0f} PUT")
            print(f"   Expiration: {parameters['dte']} days")
            print(f"   Cost: ${parameters['total_cost']:.2f}")
            print(f"2. Set stop loss at 50% of premium paid")
            print(f"3. Target: Price moves below ${parameters['breakeven']:.2f}")
        
        elif strategy == 'BULL_CALL_SPREAD':
            print(f"1. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['long_strike']:.0f} CALL")
            print(f"2. SELL TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['short_strike']:.0f} CALL")
            print(f"   Expiration: {parameters['dte']} days")
            print(f"   Net Debit: ${parameters['total_debit']:.2f}")
            print(f"3. Max Profit: ${parameters['total_max_profit']:.2f} at ${parameters['short_strike']:.0f}+")
            print(f"4. Breakeven: ${parameters['breakeven']:.2f}")
        
        elif strategy == 'BEAR_PUT_SPREAD':
            print(f"1. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['long_strike']:.0f} PUT")
            print(f"2. SELL TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['short_strike']:.0f} PUT")
            print(f"   Expiration: {parameters['dte']} days")
            print(f"   Net Debit: ${parameters['total_debit']:.2f}")
            print(f"3. Max Profit: ${parameters['total_max_profit']:.2f} at ${parameters['short_strike']:.0f}-")
            print(f"4. Breakeven: ${parameters['breakeven']:.2f}")
        
        elif strategy == 'LONG_STRADDLE':
            print(f"1. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['strike']:.0f} CALL (${parameters['call_cost']:.2f})")
            print(f"2. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['strike']:.0f} PUT (${parameters['put_cost']:.2f})")
            print(f"   Expiration: {parameters['dte']} days")
            print(f"   Total Cost: ${parameters['total_cost']:.2f}")
            print(f"3. Breakeven Range: ${parameters['breakeven_down']:.2f} - ${parameters['breakeven_up']:.2f}")
            print(f"4. Profit on big move in either direction")
        
        elif strategy == 'LONG_STRANGLE':
            print(f"1. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['call_strike']:.0f} CALL (${parameters['call_cost']:.2f})")
            print(f"2. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['put_strike']:.0f} PUT (${parameters['put_cost']:.2f})")
            print(f"   Expiration: {parameters['dte']} days")
            print(f"   Total Cost: ${parameters['total_cost']:.2f}")
            print(f"3. Breakeven Range: ${parameters['breakeven_down']:.2f} - ${parameters['breakeven_up']:.2f}")
            print(f"4. Profit on big move in either direction")
        
        elif strategy == 'IRON_CONDOR':
            print(f"1. SELL TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['put_short_strike']:.0f} PUT")
            print(f"2. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['put_long_strike']:.0f} PUT")
            print(f"3. SELL TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['call_short_strike']:.0f} CALL")
            print(f"4. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['call_long_strike']:.0f} CALL")
            print(f"   Expiration: {parameters['dte']} days")
            print(f"   Net Credit: ${parameters['total_credit']:.2f}")
            print(f"5. Profit Zone: ${parameters['breakeven_down']:.2f} - ${parameters['breakeven_up']:.2f}")
            print(f"6. Manage at 50% profit or 21 DTE")
        
        elif strategy == 'IRON_BUTTERFLY':
            print(f"1. SELL TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['center_strike']:.0f} PUT")
            print(f"2. SELL TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['center_strike']:.0f} CALL")
            print(f"3. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['long_put_strike']:.0f} PUT")
            print(f"4. BUY TO OPEN: {parameters['contracts']} contract(s)")
            print(f"   ${parameters['long_call_strike']:.0f} CALL")
            print(f"   Expiration: {parameters['dte']} days")
            print(f"   Net Credit: ${parameters['total_credit']:.2f}")
            print(f"5. Profit Zone: ${parameters['breakeven_down']:.2f} - ${parameters['breakeven_up']:.2f}")
            print(f"6. Manage at 50% profit or 21 DTE")
        
        else:
            print(f"See parameters above for {strategy} execution details")
        
    except Exception as e:
        print(f"❌ Error generating parameters: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print(f"\n{'=' * 70}")
    print("TEST COMPLETE ✅")
    print(f"{'=' * 70}")
    print(f"\n🎯 Strategy: {strategy} ({confidence:.1%} confidence)")
    print(f"💰 Total Capital Required: ${parameters.get('total_cost', parameters.get('total_debit', 0)):.2f}")
    print(f"📊 Risk/Reward: {parameters.get('risk_reward_ratio', 'N/A')}")
    print(f"🎲 Contracts: {parameters.get('contracts', 1)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
