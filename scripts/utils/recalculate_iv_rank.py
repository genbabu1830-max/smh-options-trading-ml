"""
Recalculate IV Rank Properly
Fix the broken iv_rank values from Massive.com API
"""

import pandas as pd
import numpy as np


def recalculate_iv_rank(df, lookback_days=252):
    """
    Recalculate IV Rank using proper formula
    
    IV Rank = (Current IV - 52w Low) / (52w High - 52w Low) × 100
    
    Args:
        df: DataFrame with 'date' and 'iv_atm' columns
        lookback_days: Rolling window for min/max (default 252 = 1 year)
    
    Returns:
        Series with corrected IV Rank values (0-100)
    """
    # Sort by date
    df = df.sort_values('date').copy()
    
    # Calculate rolling 52-week high and low
    df['iv_52w_high'] = df['iv_atm'].rolling(window=lookback_days, min_periods=30).max()
    df['iv_52w_low'] = df['iv_atm'].rolling(window=lookback_days, min_periods=30).min()
    
    # Calculate IV Rank
    df['iv_rank_corrected'] = (
        (df['iv_atm'] - df['iv_52w_low']) / 
        (df['iv_52w_high'] - df['iv_52w_low']) * 100
    )
    
    # Handle edge cases
    # If high == low (no variation), set to 50 (neutral)
    df.loc[df['iv_52w_high'] == df['iv_52w_low'], 'iv_rank_corrected'] = 50.0
    
    # Clip to 0-100 range
    df['iv_rank_corrected'] = df['iv_rank_corrected'].clip(0, 100)
    
    return df['iv_rank_corrected']


def compare_iv_metrics(features_path):
    """
    Compare iv_rank, iv_percentile, and corrected iv_rank
    """
    df = pd.read_csv(features_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Recalculate IV Rank
    df['iv_rank_corrected'] = recalculate_iv_rank(df)
    
    print("=" * 70)
    print("IV METRICS COMPARISON")
    print("=" * 70)
    print()
    
    # Compare distributions
    metrics = ['iv_rank', 'iv_percentile', 'iv_rank_corrected']
    
    for metric in metrics:
        if metric in df.columns:
            print(f"{metric}:")
            print(f"  Min:    {df[metric].min():.2f}")
            print(f"  Max:    {df[metric].max():.2f}")
            print(f"  Mean:   {df[metric].mean():.2f}")
            print(f"  Std:    {df[metric].std():.2f}")
            print(f"  Unique: {df[metric].nunique()}")
            print(f"  > 50:   {(df[metric] > 50).sum()} days")
            print(f"  > 70:   {(df[metric] > 70).sum()} days")
            print(f"  < 30:   {(df[metric] < 30).sum()} days")
            print()
    
    # Check correlation
    print("Correlations:")
    if 'iv_rank_corrected' in df.columns and 'iv_percentile' in df.columns:
        corr = df['iv_rank_corrected'].corr(df['iv_percentile'])
        print(f"  iv_rank_corrected vs iv_percentile: {corr:.3f}")
    print()
    
    # Save corrected version
    output_path = features_path.replace('.csv', '_with_corrected_iv.csv')
    df.to_csv(output_path, index=False)
    print(f"✓ Saved corrected data to: {output_path}")
    
    return df


if __name__ == '__main__':
    features_path = 'data/processed/smh_daily_features.csv'
    df = compare_iv_metrics(features_path)
