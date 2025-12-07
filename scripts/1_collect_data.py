#!/usr/bin/env python3
"""
Collect 2 Years of Historical SMH Options Data
Date Range: December 8, 2023 → December 5, 2024

Filters:
- Strikes: ±15% from current price
- DTE: 7-90 days only
- Volume: > 10 (proxy for liquid options)
"""

import os
import boto3
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from polygon import RESTClient
from scripts.utils.calculate_greeks import get_historical_greeks_iv
from scripts.utils.feature_engineering import engineer_all_features
import time

# Load environment variables
load_dotenv()

# Configuration
MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY")
MASSIVE_ACCESS_KEY_ID = os.getenv("MASSIVE_ACCESS_KEY_ID")
MASSIVE_SECRET_ACCESS_KEY = os.getenv("MASSIVE_SECRET_ACCESS_KEY")
MASSIVE_S3_ENDPOINT = os.getenv("MASSIVE_S3_ENDPOINT")
MASSIVE_S3_BUCKET = os.getenv("MASSIVE_S3_BUCKET")

# Date range
START_DATE = datetime(2023, 12, 8)
END_DATE = datetime(2025, 12, 5)  # Extended to December 5, 2025 (today)

# Output directory
OUTPUT_DIR = "smh_historical_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*70)
print("SMH OPTIONS HISTORICAL DATA COLLECTION")
print("="*70)
print(f"\nDate Range: {START_DATE.strftime('%Y-%m-%d')} → {END_DATE.strftime('%Y-%m-%d')}")
print(f"Duration: ~24 months (~500 trading days)")
print(f"\nFilters:")
print(f"  - Strikes: ±30% from current price (widened for strategy support)")
print(f"  - DTE: 7-90 days")
print(f"  - Volume: > 5 (lowered for more OTM options)")
print()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=MASSIVE_ACCESS_KEY_ID,
    aws_secret_access_key=MASSIVE_SECRET_ACCESS_KEY,
    endpoint_url=MASSIVE_S3_ENDPOINT
)

# Initialize Polygon client
polygon_client = RESTClient(MASSIVE_API_KEY)


def get_trading_days(start_date, end_date):
    """Generate list of trading days (Mon-Fri)"""
    trading_days = []
    current = start_date
    
    while current <= end_date:
        if current.weekday() < 5:  # Monday=0, Friday=4
            trading_days.append(current)
        current += timedelta(days=1)
    
    return trading_days


def load_stock_history(end_date, days=60):
    """Load stock history for technical indicators"""
    all_stock_data = []
    current_date = end_date
    days_collected = 0
    days_attempted = 0
    
    while days_collected < days and days_attempted < days * 2:
        if current_date.weekday() < 5:
            year = current_date.strftime('%Y')
            month = current_date.strftime('%m')
            day = current_date.strftime('%Y-%m-%d')
            
            try:
                s3_key = f"us_stocks_sip/day_aggs_v1/{year}/{month}/{day}.csv.gz"
                response = s3_client.get_object(Bucket=MASSIVE_S3_BUCKET, Key=s3_key)
                stock_df = pd.read_csv(response['Body'], compression='gzip')
                stock_df['date'] = current_date
                all_stock_data.append(stock_df)
                days_collected += 1
            except:
                pass
        
        current_date -= timedelta(days=1)
        days_attempted += 1
    
    if len(all_stock_data) > 0:
        stock_df_combined = pd.concat(all_stock_data, ignore_index=True)
        stock_df_combined = stock_df_combined.sort_values('date')
        
        # Add window_start for compatibility
        if 'window_start' not in stock_df_combined.columns:
            stock_df_combined['window_start'] = stock_df_combined['date'].astype('int64') // 10**9
        
        return stock_df_combined
    else:
        return None


def parse_option_ticker(ticker):
    """Parse SMH option ticker"""
    ticker_clean = ticker.replace('O:', '')
    
    # Find underlying (SMH = 3 chars)
    underlying_end = 0
    for i, char in enumerate(ticker_clean):
        if char.isdigit():
            underlying_end = i
            break
    
    underlying = ticker_clean[:underlying_end]
    date_str = ticker_clean[underlying_end:underlying_end+6]
    option_type = ticker_clean[underlying_end+6]
    strike_str = ticker_clean[underlying_end+7:]
    
    try:
        strike = float(strike_str) / 1000
    except ValueError:
        strike = 0.0
    
    return {
        'underlying': underlying,
        'expiration': f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}",
        'type': 'call' if option_type == 'C' else 'put',
        'strike': strike
    }


def filter_options(options_df, current_price, date):
    """
    Apply filters - WIDENED for strategy support:
    - Strikes: ±30% from current price (was ±15%)
    - DTE: 7-90 days
    - Volume: > 5 (was > 10, lowered to include more OTM options)
    
    This ensures we have:
    - OTM puts below current price (for Iron Condors)
    - OTM calls above current price (for Iron Condors)
    - Full option chain for all strategies
    """
    # Parse tickers
    parsed_data = options_df['ticker'].apply(parse_option_ticker)
    parsed_df = pd.DataFrame(parsed_data.tolist())
    
    options_df['underlying'] = parsed_df['underlying'].values
    options_df['expiration'] = parsed_df['expiration'].values
    options_df['type'] = parsed_df['type'].values
    options_df['strike'] = parsed_df['strike'].values
    
    # Calculate DTE
    options_df['expiration_date'] = pd.to_datetime(options_df['expiration'])
    options_df['dte'] = (options_df['expiration_date'] - date).dt.days
    
    # Apply WIDENED filters
    strike_min = current_price * 0.70  # 30% below (was 15%)
    strike_max = current_price * 1.30  # 30% above (was 15%)
    
    filtered = options_df[
        (options_df['strike'] >= strike_min) &
        (options_df['strike'] <= strike_max) &
        (options_df['dte'] >= 7) &
        (options_df['dte'] <= 90) &
        (options_df['volume'] > 5)  # Lowered from 10 to 5
    ].copy()
    
    return filtered


def process_single_day(date):
    """Process options data for a single day"""
    
    # Load stock history (60 days)
    stock_data = load_stock_history(date, days=60)
    if stock_data is None:
        return None, "No stock data"
    
    # Get current SMH price
    smh_data = stock_data[stock_data['ticker'] == 'SMH']
    if len(smh_data) == 0:
        return None, "No SMH price"
    
    current_price = smh_data[smh_data['date'] == date]['close'].iloc[0] if len(smh_data[smh_data['date'] == date]) > 0 else smh_data['close'].iloc[-1]
    
    # Load SMH options
    year = date.strftime('%Y')
    month = date.strftime('%m')
    day = date.strftime('%Y-%m-%d')
    
    try:
        s3_key = f"us_options_opra/day_aggs_v1/{year}/{month}/{day}.csv.gz"
        response = s3_client.get_object(Bucket=MASSIVE_S3_BUCKET, Key=s3_key)
        options_df = pd.read_csv(response['Body'], compression='gzip')
        
        # Filter for SMH options (standard format only)
        options_df = options_df[options_df['ticker'].str.match(r'^O:SMH\d{6}[CP]\d{8}$')]
        
        if len(options_df) == 0:
            return None, "No SMH options"
        
    except Exception as e:
        return None, f"Error loading options: {e}"
    
    # Apply filters
    filtered_options = filter_options(options_df, current_price, date)
    
    if len(filtered_options) == 0:
        return None, "No options after filtering"
    
    # Calculate Greeks
    greeks_data = []
    api_count = 0
    calc_count = 0
    
    for idx, row in filtered_options.iterrows():
        ticker = row['ticker']
        
        # Try API first
        try:
            snapshot = polygon_client.get_snapshot_option("SMH", ticker)
            opt = snapshot
            api_count += 1
            
            greeks_data.append({
                'ticker': ticker,
                'strike': row['strike'],
                'expiration': row['expiration'],
                'type': row['type'],
                'delta': opt.greeks.delta if opt.greeks else None,
                'gamma': opt.greeks.gamma if opt.greeks else None,
                'theta': opt.greeks.theta if opt.greeks else None,
                'vega': opt.greeks.vega if opt.greeks else None,
                'implied_volatility': opt.implied_volatility if opt.implied_volatility else None,
                'open_interest': opt.open_interest if opt.open_interest else None,
            })
            
            # Rate limiting
            time.sleep(0.1)
            
        except:
            # Calculate Greeks
            try:
                contract_df = pd.DataFrame([{
                    'ticker': row['ticker'],
                    'strike': row['strike'],
                    'type': row['type'],
                    'expiration': row['expiration'],
                    'close': row['close']
                }])
                
                calculated_greeks = get_historical_greeks_iv(contract_df, current_price, date)
                
                if len(calculated_greeks) > 0:
                    calc = calculated_greeks.iloc[0]
                    calc_count += 1
                    
                    greeks_data.append({
                        'ticker': row['ticker'],
                        'strike': row['strike'],
                        'expiration': row['expiration'],
                        'type': row['type'],
                        'delta': calc['delta'],
                        'gamma': calc['gamma'],
                        'theta': calc['theta'],
                        'vega': calc['vega'],
                        'implied_volatility': calc['implied_volatility'],
                        'open_interest': None,
                    })
            except:
                pass
    
    if len(greeks_data) == 0:
        return None, "No Greeks calculated"
    
    greeks_df = pd.DataFrame(greeks_data)
    
    # Merge with OHLCV
    merged_df = pd.merge(
        filtered_options,
        greeks_df[['strike', 'expiration', 'type', 'delta', 'gamma', 'theta', 'vega', 
                   'implied_volatility', 'open_interest']],
        on=['strike', 'expiration', 'type'],
        how='left'
    )
    
    # Calculate break-even
    merged_df['break_even_price'] = merged_df.apply(
        lambda row: row['strike'] + row['close'] if row['type'] == 'call' else row['strike'] - row['close'],
        axis=1
    )
    
    # Calculate market features
    market_features = engineer_all_features(
        date=date,
        options_df=merged_df,
        stock_df=stock_data
    )
    
    # Add market features to each row
    feature_cols_to_add = [k for k in market_features.keys() if k not in ['date']]
    for feature_name in feature_cols_to_add:
        merged_df[feature_name] = market_features[feature_name]
    
    stats = {
        'date': date,
        'contracts_before_filter': len(options_df),
        'contracts_after_filter': len(filtered_options),
        'contracts_with_greeks': len(greeks_df),
        'api_greeks': api_count,
        'calculated_greeks': calc_count,
        'current_price': current_price
    }
    
    return merged_df, stats


def main():
    """Main collection loop"""
    
    # Get trading days
    trading_days = get_trading_days(START_DATE, END_DATE)
    total_days = len(trading_days)
    
    print(f"Total trading days to process: {total_days}")
    print()
    
    all_data = []
    stats_log = []
    checkpoint_interval = 50
    
    start_time = time.time()
    
    for day_num, date in enumerate(trading_days, 1):
        print(f"[{day_num}/{total_days}] Processing {date.strftime('%Y-%m-%d')}...", end=" ")
        
        result, stats = process_single_day(date)
        
        if result is not None:
            all_data.append(result)
            stats_log.append(stats)
            print(f"✓ {stats['contracts_after_filter']} contracts ({stats['api_greeks']} API, {stats['calculated_greeks']} calc)")
        else:
            print(f"✗ {stats}")
        
        # Checkpoint every 50 days
        if day_num % checkpoint_interval == 0:
            if len(all_data) > 0:
                checkpoint_df = pd.concat(all_data, ignore_index=True)
                checkpoint_file = f"{OUTPUT_DIR}/smh_checkpoint_{day_num}.csv"
                checkpoint_df.to_csv(checkpoint_file, index=False)
                print(f"  → Checkpoint saved: {len(checkpoint_df)} total rows")
    
    # Save final dataset
    if len(all_data) > 0:
        final_df = pd.concat(all_data, ignore_index=True)
        final_file = f"{OUTPUT_DIR}/smh_complete_dataset.csv"
        final_df.to_csv(final_file, index=False)
        
        # Save stats
        stats_df = pd.DataFrame(stats_log)
        stats_file = f"{OUTPUT_DIR}/smh_collection_stats.csv"
        stats_df.to_csv(stats_file, index=False)
        
        elapsed = time.time() - start_time
        
        print()
        print("="*70)
        print("COLLECTION COMPLETE")
        print("="*70)
        print(f"Total days processed: {len(stats_log)}")
        print(f"Total contracts: {len(final_df)}")
        print(f"Total columns: {len(final_df.columns)}")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        print(f"\nFiles saved:")
        print(f"  - {final_file}")
        print(f"  - {stats_file}")
        print("="*70)
    else:
        print("\n✗ No data collected")


if __name__ == "__main__":
    main()
