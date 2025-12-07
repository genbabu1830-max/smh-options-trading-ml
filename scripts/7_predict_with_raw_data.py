#!/usr/bin/env python3
"""
Production Prediction Script - Takes Raw Data as Input
======================================================

This script demonstrates the complete production workflow:
1. Accept raw option chain + price history as input
2. Extract 84 features using FeatureExtractor
3. Predict strategy using trained ML model
4. Generate parameters using backtesting (Stage 2)

Usage:
    python scripts/7_predict_with_raw_data.py --date 2024-12-05
    python scripts/7_predict_with_raw_data.py --live
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.feature_extractor import FeatureExtractor


def load_model():
    """Load the trained ML model."""
    print("Loading trained model...")
    
    with open('models/lightgbm_clean_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    with open('models/label_encoder_clean.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    
    print(f"✓ Model loaded: LightGBM (84.21% accuracy)")
    return model, label_encoder


def load_raw_data(date=None):
    """
    Load raw market data for prediction.
    
    In production, this would:
    - Fetch current option chain from broker API
    - Get price history from market data provider
    - Retrieve SPY/VIX data
    
    For demo, we load from historical data files.
    """
    print(f"\nLoading raw market data for {date}...")
    
    # Load SMH price history
    price_history = pd.read_csv('data/smh_historical_data.csv')
    price_history['date'] = pd.to_datetime(price_history['date']).dt.strftime('%Y-%m-%d')
    
    # Load option chain for the date
    # In production, this would be today's live option chain
    option_chain = pd.read_csv('data/smh_options_data.csv')
    option_chain = option_chain[option_chain['quote_date'] == date].copy()
    
    if len(option_chain) == 0:
        raise ValueError(f"No option chain data found for {date}")
    
    # Rename columns to match FeatureExtractor expectations
    option_chain = option_chain.rename(columns={
        'option_type': 'type',
        'days_to_expiration': 'dte',
        'implied_volatility': 'iv'
    })
    
    # Load SPY data (optional)
    try:
        spy_history = pd.read_csv('data/spy_historical_data.csv')
        spy_history['date'] = pd.to_datetime(spy_history['date']).dt.strftime('%Y-%m-%d')
    except FileNotFoundError:
        spy_history = None
        print("  ⚠ SPY data not found, using defaults")
    
    # Load VIX data (optional)
    try:
        vix_history = pd.read_csv('data/vix_historical_data.csv')
        vix_history['date'] = pd.to_datetime(vix_history['date']).dt.strftime('%Y-%m-%d')
    except FileNotFoundError:
        vix_history = None
        print("  ⚠ VIX data not found, using defaults")
    
    print(f"✓ Loaded {len(price_history)} days of price history")
    print(f"✓ Loaded {len(option_chain)} option contracts")
    
    return option_chain, price_history, spy_history, vix_history


def main():
    parser = argparse.ArgumentParser(description='Predict strategy from raw market data')
    parser.add_argument('--date', type=str, help='Date for prediction (YYYY-MM-DD)')
    parser.add_argument('--live', action='store_true', help='Use latest available data')
    parser.add_argument('--save', type=str, help='Save prediction to file')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("SMH OPTIONS STRATEGY PREDICTION - RAW DATA INPUT")
    print("=" * 70)
    
    # Determine date
    if args.live:
        # In production, this would be today's date
        # For demo, use latest date in data
        price_data = pd.read_csv('data/smh_historical_data.csv')
        date = price_data['date'].max()
        print(f"\n📅 Using latest available date: {date}")
    elif args.date:
        date = args.date
        print(f"\n📅 Using specified date: {date}")
    else:
        print("\n❌ Error: Must specify --date or --live")
        sys.exit(1)
    
    # STAGE 0: Load raw market data
    print("\n" + "=" * 70)
    print("STAGE 0: LOAD RAW MARKET DATA")
    print("=" * 70)
    
    option_chain, price_history, spy_history, vix_history = load_raw_data(date)
    
    # STAGE 1: Extract features from raw data
    print("\n" + "=" * 70)
    print("STAGE 1: EXTRACT FEATURES")
    print("=" * 70)
    
    extractor = FeatureExtractor()
    print("Extracting 84 features from raw data...")
    
    features = extractor.extract_features(
        option_chain=option_chain,
        price_history=price_history,
        current_date=date,
        spy_history=spy_history,
        vix_history=vix_history
    )
    
    print(f"✓ Extracted {len(features)} features")
    
    # Show key features
    print("\nKey Market Conditions:")
    print(f"  Current Price: ${features['current_price']:.2f}")
    print(f"  IV Rank: {features['iv_rank']:.1f}%")
    print(f"  ADX: {features['adx_14']:.1f}")
    print(f"  RSI: {features['rsi_14']:.1f}")
    print(f"  Trend Regime: {features['trend_regime']} (0=strong_down, 4=strong_up)")
    print(f"  Volatility Regime: {features['volatility_regime']} (0=very_low, 4=very_high)")
    
    # STAGE 2: Predict strategy using ML model
    print("\n" + "=" * 70)
    print("STAGE 2: PREDICT STRATEGY (ML MODEL)")
    print("=" * 70)
    
    model, label_encoder = load_model()
    
    # Convert features to model input format
    feature_df = extractor.get_feature_dataframe(features)
    
    # Get prediction
    prediction = model.predict(feature_df)[0]
    probabilities = model.predict_proba(feature_df)[0]
    
    # Decode strategy name
    strategy = label_encoder.inverse_transform([prediction])[0]
    confidence = probabilities[prediction]
    
    print(f"\n🎯 PREDICTED STRATEGY: {strategy}")
    print(f"   Confidence: {confidence:.1%}")
    
    # Show top 3 alternatives
    top_3_idx = np.argsort(probabilities)[-3:][::-1]
    print("\n   Top 3 Strategies:")
    for i, idx in enumerate(top_3_idx, 1):
        strat_name = label_encoder.inverse_transform([idx])[0]
        prob = probabilities[idx]
        print(f"   {i}. {strat_name}: {prob:.1%}")
    
    # STAGE 3: Generate parameters (simplified - would use backtesting)
    print("\n" + "=" * 70)
    print("STAGE 3: GENERATE PARAMETERS (BACKTESTING)")
    print("=" * 70)
    print("\n⚠ Parameter generation requires historical backtesting")
    print("   See scripts/6_predict_strategy.py for full implementation")
    
    # Create output
    output = {
        'prediction_date': date,
        'prediction_time': datetime.now().isoformat(),
        'model_version': 'v1.0',
        'strategy': {
            'type': strategy,
            'confidence': float(confidence)
        },
        'market_conditions': {
            'current_price': float(features['current_price']),
            'iv_rank': float(features['iv_rank']),
            'adx': float(features['adx_14']),
            'rsi': float(features['rsi_14']),
            'trend_regime': int(features['trend_regime']),
            'volatility_regime': int(features['volatility_regime'])
        },
        'top_3_strategies': [
            {
                'strategy': label_encoder.inverse_transform([idx])[0],
                'confidence': float(probabilities[idx])
            }
            for idx in top_3_idx
        ]
    }
    
    # Save if requested
    if args.save:
        with open(args.save, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n✓ Prediction saved to {args.save}")
    
    print("\n" + "=" * 70)
    print("PREDICTION COMPLETE")
    print("=" * 70)
    
    return output


if __name__ == "__main__":
    main()
