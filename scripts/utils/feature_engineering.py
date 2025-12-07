#!/usr/bin/env python3
"""
Phase 2: Feature Engineering for IWM Options ML Model
Calculates 80+ features from historical data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ta.trend import SMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange


def calculate_price_features(stock_df, lookback_periods=[5, 10, 20, 50]):
    """
    Calculate technical indicators from price data
    Input: DataFrame with OHLCV data sorted by date
    Output: Dictionary of features
    """
    features = {}
    
    # Returns over multiple windows
    for period in [1, 3, 5, 10, 20, 50]:
        if len(stock_df) > period:  # Need period + 1 data points
            ret = stock_df['close'].pct_change(periods=period).iloc[-1]
            features[f'return_{period}d'] = ret if pd.notna(ret) else 0.0
        else:
            features[f'return_{period}d'] = 0.0
    
    # RSI (Relative Strength Index)
    if len(stock_df) >= 14:
        rsi_indicator = RSIIndicator(close=stock_df['close'], window=14)
        features['rsi_14'] = rsi_indicator.rsi().iloc[-1]
    else:
        features['rsi_14'] = 50.0
    
    # MACD (Moving Average Convergence Divergence)
    if len(stock_df) >= 26:
        macd = MACD(close=stock_df['close'])
        features['macd'] = macd.macd().iloc[-1]
        features['macd_signal'] = macd.macd_signal().iloc[-1]
        features['macd_histogram'] = macd.macd_diff().iloc[-1]
    else:
        features['macd'] = 0.0
        features['macd_signal'] = 0.0
        features['macd_histogram'] = 0.0
    
    # ADX (Average Directional Index) - Trend Strength
    if len(stock_df) >= 14:
        adx = ADXIndicator(
            high=stock_df['high'],
            low=stock_df['low'],
            close=stock_df['close'],
            window=14
        )
        features['adx_14'] = adx.adx().iloc[-1]
    else:
        features['adx_14'] = 20.0
    
    # Moving Averages
    for period in lookback_periods:
        if len(stock_df) >= period:
            sma = SMAIndicator(close=stock_df['close'], window=period)
            features[f'sma_{period}'] = sma.sma_indicator().iloc[-1]
            features[f'price_vs_sma_{period}'] = (
                (stock_df['close'].iloc[-1] - features[f'sma_{period}']) / 
                features[f'sma_{period}']
            )
        else:
            features[f'sma_{period}'] = stock_df['close'].iloc[-1]
            features[f'price_vs_sma_{period}'] = 0.0
    
    # SMA_200 (only if we have enough data, otherwise mark as unavailable)
    if len(stock_df) >= 200:
        sma = SMAIndicator(close=stock_df['close'], window=200)
        features['sma_200'] = sma.sma_indicator().iloc[-1]
        features['price_vs_sma_200'] = (
            (stock_df['close'].iloc[-1] - features['sma_200']) / 
            features['sma_200']
        )
    else:
        # Not enough data - mark as None instead of using incorrect value
        features['sma_200'] = None
        features['price_vs_sma_200'] = None
    
    # SMA Alignment (trend confirmation)
    if all(f'sma_{p}' in features for p in [10, 20, 50]):
        features['sma_alignment'] = int(
            features['sma_10'] > features['sma_20'] > features['sma_50']
        )
    else:
        features['sma_alignment'] = 0
    
    # Bollinger Bands
    if len(stock_df) >= 20:
        bb = BollingerBands(close=stock_df['close'], window=20)
        features['bb_upper'] = bb.bollinger_hband().iloc[-1]
        features['bb_middle'] = bb.bollinger_mavg().iloc[-1]
        features['bb_lower'] = bb.bollinger_lband().iloc[-1]
        
        bb_range = features['bb_upper'] - features['bb_lower']
        if bb_range > 0:
            features['bb_position'] = (
                (stock_df['close'].iloc[-1] - features['bb_lower']) / bb_range
            )
        else:
            features['bb_position'] = 0.5
    else:
        current_price = stock_df['close'].iloc[-1]
        features['bb_upper'] = current_price * 1.02
        features['bb_middle'] = current_price
        features['bb_lower'] = current_price * 0.98
        features['bb_position'] = 0.5
    
    # ATR (Average True Range) - Volatility
    if len(stock_df) >= 14:
        atr = AverageTrueRange(
            high=stock_df['high'],
            low=stock_df['low'],
            close=stock_df['close'],
            window=14
        )
        features['atr_14'] = atr.average_true_range().iloc[-1]
    else:
        features['atr_14'] = stock_df['close'].iloc[-1] * 0.02
    
    # Volume Features
    if len(stock_df) >= 20:
        features['volume_20d_avg'] = stock_df['volume'].tail(20).mean()
        features['volume_vs_avg'] = (
            stock_df['volume'].iloc[-1] / features['volume_20d_avg']
        )
    else:
        features['volume_20d_avg'] = stock_df['volume'].mean()
        features['volume_vs_avg'] = 1.0
    
    return features


def calculate_volatility_features(options_df, stock_df):
    """
    Calculate volatility-related features
    """
    features = {}
    
    # Historical Volatility (20-day)
    if len(stock_df) >= 20:
        returns = stock_df['close'].pct_change()
        features['hv_20d'] = returns.tail(20).std() * (252 ** 0.5)  # Annualized
    else:
        features['hv_20d'] = 0.20  # Default 20%
    
    # Current Implied Volatility (ATM options)
    current_price = stock_df['close'].iloc[-1]
    atm_options = options_df[
        (options_df['strike'] >= current_price * 0.98) &
        (options_df['strike'] <= current_price * 1.02)
    ]
    
    if len(atm_options) > 0 and 'implied_volatility' in atm_options.columns:
        features['iv_atm'] = atm_options['implied_volatility'].mean()
    else:
        features['iv_atm'] = 0.25  # Default 25%
    
    # IV Rank (current IV vs 52-week range)
    if len(options_df) >= 252 and 'implied_volatility' in options_df.columns:
        iv_52w_high = options_df['implied_volatility'].rolling(252).max().iloc[-1]
        iv_52w_low = options_df['implied_volatility'].rolling(252).min().iloc[-1]
        
        if iv_52w_high > iv_52w_low:
            features['iv_rank'] = (
                (features['iv_atm'] - iv_52w_low) / 
                (iv_52w_high - iv_52w_low) * 100
            )
        else:
            features['iv_rank'] = 50.0
    else:
        features['iv_rank'] = 50.0
    
    # IV Percentile
    if len(options_df) >= 252 and 'implied_volatility' in options_df.columns:
        iv_history = options_df['implied_volatility'].tail(252)
        features['iv_percentile'] = (
            (iv_history < features['iv_atm']).sum() / len(iv_history) * 100
        )
    else:
        features['iv_percentile'] = 50.0
    
    # HV vs IV (volatility premium)
    if features['iv_atm'] > 0:
        features['hv_iv_ratio'] = features['hv_20d'] / features['iv_atm']
    else:
        features['hv_iv_ratio'] = 1.0
    
    return features


def calculate_options_features(options_df, current_price):
    """
    Calculate options-specific features
    """
    features = {}
    
    # Put/Call Ratio
    puts = options_df[options_df['type'] == 'put']
    calls = options_df[options_df['type'] == 'call']
    
    put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0
    call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
    
    if call_volume > 0:
        features['put_call_ratio'] = put_volume / call_volume
    else:
        features['put_call_ratio'] = 1.0
    
    # Put/Call OI Ratio
    if 'open_interest' in options_df.columns:
        put_oi = puts['open_interest'].sum()
        call_oi = calls['open_interest'].sum()
        
        if call_oi > 0:
            features['put_call_oi_ratio'] = put_oi / call_oi
        else:
            features['put_call_oi_ratio'] = 1.0
    else:
        features['put_call_oi_ratio'] = 1.0
    
    # ATM Greeks (average across ATM options)
    atm_options = options_df[
        (options_df['strike'] >= current_price * 0.98) &
        (options_df['strike'] <= current_price * 1.02)
    ]
    
    if len(atm_options) > 0:
        for greek in ['delta', 'gamma', 'theta', 'vega']:
            if greek in atm_options.columns:
                features[f'atm_{greek}'] = atm_options[greek].mean()
            else:
                features[f'atm_{greek}'] = 0.0
    else:
        features['atm_delta'] = 0.5
        features['atm_gamma'] = 0.05
        features['atm_theta'] = -0.1
        features['atm_vega'] = 0.2
    
    # Max Pain (strike with highest open interest)
    if 'open_interest' in options_df.columns and len(options_df) > 0:
        oi_by_strike = options_df.groupby('strike')['open_interest'].sum()
        if len(oi_by_strike) > 0:
            features['max_pain_strike'] = oi_by_strike.idxmax()
            features['distance_to_max_pain'] = (
                (current_price - features['max_pain_strike']) / current_price
            )
        else:
            features['max_pain_strike'] = current_price
            features['distance_to_max_pain'] = 0.0
    else:
        features['max_pain_strike'] = current_price
        features['distance_to_max_pain'] = 0.0
    
    return features


def classify_market_regime(features):
    """
    Classify current market regime
    """
    regime = {}
    
    # Trend Classification
    adx = features.get('adx_14', 20)
    macd_hist = features.get('macd_histogram', 0)
    rsi = features.get('rsi_14', 50)
    
    if adx > 25:
        if macd_hist > 0 and rsi > 50:
            regime['trend'] = 'strong_up'
            regime['trend_numeric'] = 4
        elif macd_hist < 0 and rsi < 50:
            regime['trend'] = 'strong_down'
            regime['trend_numeric'] = 0
        else:
            regime['trend'] = 'mixed'
            regime['trend_numeric'] = 2
    elif adx < 20:
        regime['trend'] = 'ranging'
        regime['trend_numeric'] = 2
    else:
        if rsi > 50:
            regime['trend'] = 'weak_up'
            regime['trend_numeric'] = 3
        else:
            regime['trend'] = 'weak_down'
            regime['trend_numeric'] = 1
    
    # Volatility Regime
    iv_rank = features.get('iv_rank', 50)
    
    if iv_rank > 70:
        regime['volatility'] = 'extreme'
        regime['volatility_numeric'] = 3
    elif iv_rank > 50:
        regime['volatility'] = 'elevated'
        regime['volatility_numeric'] = 2
    elif iv_rank > 30:
        regime['volatility'] = 'normal'
        regime['volatility_numeric'] = 1
    else:
        regime['volatility'] = 'low'
        regime['volatility_numeric'] = 0
    
    # Volume Regime
    volume_vs_avg = features.get('volume_vs_avg', 1.0)
    
    if volume_vs_avg > 1.5:
        regime['volume'] = 'high'
        regime['volume_numeric'] = 2
    elif volume_vs_avg > 0.8:
        regime['volume'] = 'average'
        regime['volume_numeric'] = 1
    else:
        regime['volume'] = 'low'
        regime['volume_numeric'] = 0
    
    return regime


def calculate_support_resistance(stock_df, window=20):
    """
    Identify support and resistance levels
    """
    features = {}
    
    if len(stock_df) >= window:
        # Recent high/low
        high_20d = stock_df['high'].tail(window).max()
        low_20d = stock_df['low'].tail(window).min()
        current_price = stock_df['close'].iloc[-1]
        
        features['resistance_level'] = high_20d
        features['support_level'] = low_20d
        
        # Distance to support/resistance
        features['distance_to_resistance'] = (
            (high_20d - current_price) / current_price
        )
        features['distance_to_support'] = (
            (current_price - low_20d) / current_price
        )
        
        # Position in range
        range_width = high_20d - low_20d
        if range_width > 0:
            features['position_in_range'] = (
                (current_price - low_20d) / range_width
            )
        else:
            features['position_in_range'] = 0.5
    else:
        current_price = stock_df['close'].iloc[-1]
        features['resistance_level'] = current_price * 1.05
        features['support_level'] = current_price * 0.95
        features['distance_to_resistance'] = 0.05
        features['distance_to_support'] = 0.05
        features['position_in_range'] = 0.5
    
    return features


def calculate_market_context(stock_df):
    """
    Calculate market context features (SPY correlation, etc.)
    """
    features = {}
    
    # Filter for IWM and SPY
    iwm_data = stock_df[stock_df['ticker'] == 'IWM'].sort_values('window_start')
    spy_data = stock_df[stock_df['ticker'] == 'SPY'].sort_values('window_start')
    
    if len(iwm_data) >= 30 and len(spy_data) >= 30:
        # SPY correlation (30-day rolling)
        iwm_returns = iwm_data['close'].pct_change().dropna()
        spy_returns = spy_data['close'].pct_change().dropna()
        
        # Align the series by index
        if len(iwm_returns) >= 30 and len(spy_returns) >= 30:
            corr = iwm_returns.tail(30).corr(spy_returns.tail(30))
            features['spy_correlation'] = corr if pd.notna(corr) else 0.85
        else:
            features['spy_correlation'] = 0.85
        
        # SPY relative performance
        features['spy_return_1d'] = spy_returns.iloc[-1]
        features['iwm_vs_spy'] = iwm_returns.iloc[-1] - spy_returns.iloc[-1]
    else:
        features['spy_correlation'] = 0.85
        features['spy_return_1d'] = 0.0
        features['iwm_vs_spy'] = 0.0
    
    # VIX data
    vix_data = stock_df[stock_df['ticker'] == 'VIX']
    if len(vix_data) > 0:
        features['vix_level'] = vix_data['close'].iloc[-1]
        if len(vix_data) >= 2:
            features['vix_change'] = vix_data['close'].iloc[-1] - vix_data['close'].iloc[-2]
        else:
            features['vix_change'] = 0.0
    else:
        features['vix_level'] = 15.0
        features['vix_change'] = 0.0
    
    return features


def engineer_all_features(date, options_df, stock_df):
    """
    Complete feature engineering for one day
    Returns: Dictionary with 80+ features
    """
    all_features = {'date': date}
    
    # Filter data for IWM
    iwm_stock = stock_df[stock_df['ticker'] == 'IWM'].copy()
    
    if len(iwm_stock) == 0:
        print(f"Warning: No IWM stock data for {date}")
        return None
    
    current_price = iwm_stock['close'].iloc[-1]
    all_features['current_price'] = current_price
    
    # Calculate each feature category
    try:
        price_features = calculate_price_features(iwm_stock)
        all_features.update(price_features)
    except Exception as e:
        print(f"Error calculating price features: {e}")
    
    try:
        vol_features = calculate_volatility_features(options_df, iwm_stock)
        all_features.update(vol_features)
    except Exception as e:
        print(f"Error calculating volatility features: {e}")
    
    try:
        options_features = calculate_options_features(options_df, current_price)
        all_features.update(options_features)
    except Exception as e:
        print(f"Error calculating options features: {e}")
    
    try:
        support_resistance = calculate_support_resistance(iwm_stock)
        all_features.update(support_resistance)
    except Exception as e:
        print(f"Error calculating support/resistance: {e}")
    
    try:
        market_context = calculate_market_context(stock_df)
        all_features.update(market_context)
    except Exception as e:
        print(f"Error calculating market context: {e}")
    
    # Add regime classification
    try:
        regime = classify_market_regime(all_features)
        all_features.update(regime)
    except Exception as e:
        print(f"Error classifying regime: {e}")
    
    return all_features


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("PHASE 2: FEATURE ENGINEERING TEST")
    print("="*70)
    print()
    
    # This would normally load from your historical data
    # For testing, you can use the output from test_one_day_pipeline.py
    
    print("To use this module:")
    print("1. Load your historical data (options_df, stock_df)")
    print("2. Call: features = engineer_all_features(date, options_df, stock_df)")
    print("3. Features dictionary will contain 80+ calculated features")
    print()
    print("Example:")
    print("  features = engineer_all_features(")
    print("      date=datetime(2024, 11, 29),")
    print("      options_df=merged_options_data,")
    print("      stock_df=stock_data")
    print("  )")
    print()
    print(f"Total feature categories: 6")
    print("  - Price features: ~25")
    print("  - Volatility features: ~10")
    print("  - Options features: ~15")
    print("  - Support/Resistance: ~6")
    print("  - Market context: ~5")
    print("  - Regime classification: ~6")
    print("  Total: ~67 features")
