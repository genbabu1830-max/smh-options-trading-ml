"""
Production Prediction Script - Two-Stage System
Stage 1: ML model predicts strategy type
Stage 2: Backtesting generates optimal parameters

Usage:
    python scripts/6_predict_strategy.py --date 2024-12-06
    python scripts/6_predict_strategy.py --live  # Use today's data

Version: 1.0
Date: December 6, 2024
"""

import pandas as pd
import numpy as np
import joblib
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class StrategyPredictor:
    """Two-stage prediction system for options strategy selection"""
    
    def __init__(self):
        print("=" * 80)
        print("STRATEGY PREDICTOR - TWO-STAGE SYSTEM")
        print("=" * 80)
        print()
        
        # Load ML model (Stage 1)
        print("Loading ML model...")
        self.model = joblib.load('models/lightgbm_clean_model.pkl')
        self.label_encoder = joblib.load('models/label_encoder_clean.pkl')
        
        with open('models/feature_names_clean.json', 'r') as f:
            self.feature_names = json.load(f)
        
        print(f"  Model: LightGBM")
        print(f"  Features: {len(self.feature_names)}")
        print(f"  Strategies: {len(self.label_encoder.classes_)}")
        print()
        
        self.strategy_names = self.label_encoder.classes_.tolist()
    
    def load_market_data(self, date=None):
        """Load market data for a specific date"""
        print("Loading market data...")
        
        # Load processed features
        df = pd.read_csv('data/processed/smh_daily_features.csv')
        df['date'] = pd.to_datetime(df['date'])
        
        if date:
            target_date = pd.to_datetime(date)
            data = df[df['date'] == target_date]
            
            if len(data) == 0:
                print(f"  ⚠️  No data found for {date}")
                print(f"  Available dates: {df['date'].min()} to {df['date'].max()}")
                return None
        else:
            # Use most recent date
            data = df.iloc[[-1]]
            target_date = data['date'].iloc[0]
        
        print(f"  Date: {target_date.strftime('%Y-%m-%d')}")
        print(f"  Features loaded: {len(data.columns)}")
        print()
        
        return data
    
    def predict_strategy(self, market_data):
        """Stage 1: Predict strategy type using ML model"""
        print("=" * 80)
        print("STAGE 1: STRATEGY PREDICTION (ML MODEL)")
        print("=" * 80)
        print()
        
        # Extract features in correct order
        features = market_data[self.feature_names].values
        
        # Handle missing values (fill with median from training)
        if np.any(np.isnan(features)):
            print("  ⚠️  Warning: Missing values detected, filling with median")
            features = np.nan_to_num(features, nan=0.0)
        
        # Predict
        strategy_idx = self.model.predict(features)[0]
        strategy_proba = self.model.predict_proba(features)[0]
        
        # Get predicted strategy
        strategy_name = self.label_encoder.inverse_transform([strategy_idx])[0]
        confidence = strategy_proba[strategy_idx]
        
        print(f"✅ Predicted Strategy: {strategy_name}")
        print(f"   Confidence: {confidence:.1%}")
        print()
        
        # Get top 3 predictions
        top3_idx = np.argsort(strategy_proba)[-3:][::-1]
        top3_strategies = self.label_encoder.inverse_transform(top3_idx)
        top3_proba = strategy_proba[top3_idx]
        
        print("Top 3 Predictions:")
        for i, (strat, prob) in enumerate(zip(top3_strategies, top3_proba), 1):
            marker = "👑" if i == 1 else "  "
            print(f"  {marker} {i}. {strat:20s}: {prob:6.1%}")
        print()
        
        # Show key market conditions
        print("Key Market Conditions:")
        print(f"  Current Price: ${market_data['current_price'].iloc[0]:.2f}")
        print(f"  IV Rank: {market_data['iv_rank'].iloc[0]:.1f}")
        print(f"  ADX: {market_data['adx_14'].iloc[0]:.1f}")
        print(f"  RSI: {market_data['rsi_14'].iloc[0]:.1f}")
        print(f"  Trend Regime: {int(market_data['trend_regime'].iloc[0])}")
        print(f"  Volatility Regime: {int(market_data['volatility_regime'].iloc[0])}")
        print()
        
        return {
            'strategy': strategy_name,
            'confidence': float(confidence),
            'top3_strategies': top3_strategies.tolist(),
            'top3_probabilities': top3_proba.tolist(),
            'all_probabilities': strategy_proba.tolist()
        }
    
    def generate_parameters(self, strategy, market_data):
        """Stage 2: Generate strategy parameters using backtesting logic"""
        print("=" * 80)
        print("STAGE 2: PARAMETER GENERATION (BACKTESTING)")
        print("=" * 80)
        print()
        
        print(f"Generating parameters for: {strategy}")
        print()
        
        # Load training data to find similar days
        training_data = pd.read_csv('data/processed/smh_training_data.csv')
        
        # Extract current conditions
        current_price = market_data['current_price'].iloc[0]
        iv_rank = market_data['iv_rank'].iloc[0]
        adx = market_data['adx_14'].iloc[0]
        trend_regime = int(market_data['trend_regime'].iloc[0])
        
        # Find similar historical days
        print("Finding similar historical days...")
        similar_mask = (
            (abs(training_data['iv_rank'] - iv_rank) < 10) &
            (abs(training_data['adx_14'] - adx) < 5) &
            (training_data['trend_regime'] == trend_regime)
        )
        
        similar_days = training_data[similar_mask]
        print(f"  Found {len(similar_days)} similar days")
        
        if len(similar_days) < 10:
            print("  ⚠️  Warning: Few similar days found, using broader criteria")
            similar_mask = (abs(training_data['iv_rank'] - iv_rank) < 20)
            similar_days = training_data[similar_mask]
            print(f"  Found {len(similar_days)} days with similar IV")
        
        print()
        
        # Get parameters from similar days with same strategy
        strategy_days = similar_days[similar_days['strategy'] == strategy]
        
        if len(strategy_days) > 0:
            print(f"Found {len(strategy_days)} historical days with {strategy}")
            
            # Use median parameters from successful historical trades
            parameters = self._extract_parameters(strategy, strategy_days, current_price)
        else:
            print(f"No historical {strategy} trades found, using default parameters")
            parameters = self._default_parameters(strategy, current_price, iv_rank)
        
        print()
        print("Generated Parameters:")
        for key, value in parameters.items():
            if isinstance(value, float):
                print(f"  {key:20s}: {value:.2f}")
            else:
                print(f"  {key:20s}: {value}")
        print()
        
        return parameters
    
    def _extract_parameters(self, strategy, historical_data, current_price):
        """Extract optimal parameters from historical data"""
        
        # Strategy-specific parameter extraction
        if strategy in ['BULL_CALL_SPREAD', 'BEAR_PUT_SPREAD']:
            # Use median strikes from historical trades
            long_strike = historical_data['long_strike'].median()
            short_strike = historical_data['short_strike'].median()
            dte = int(historical_data['dte'].median())
            
            # Adjust to current price
            if not np.isnan(long_strike) and not np.isnan(short_strike):
                spread_width = abs(short_strike - long_strike)
                
                if strategy == 'BULL_CALL_SPREAD':
                    long_strike = round(current_price * 0.98 / 5) * 5  # Slightly ITM
                    short_strike = long_strike + spread_width
                else:  # BEAR_PUT_SPREAD
                    short_strike = round(current_price * 1.02 / 5) * 5  # Slightly ITM
                    long_strike = short_strike - spread_width
            else:
                # Defaults if no historical data
                if strategy == 'BULL_CALL_SPREAD':
                    long_strike = round(current_price * 0.98 / 5) * 5
                    short_strike = long_strike + 10
                else:
                    short_strike = round(current_price * 1.02 / 5) * 5
                    long_strike = short_strike - 10
                dte = 21
            
            return {
                'long_strike': float(long_strike),
                'short_strike': float(short_strike),
                'dte': dte,
                'contracts': 1
            }
        
        elif strategy in ['IRON_CONDOR', 'IRON_BUTTERFLY']:
            # Use median strikes
            center = historical_data['center_strike'].median()
            dte = int(historical_data['dte'].median())
            
            if np.isnan(center):
                center = round(current_price / 5) * 5
                dte = 30
            
            # Calculate wing strikes
            if strategy == 'IRON_CONDOR':
                wing_width = 10
                short_put = center - 5
                long_put = short_put - wing_width
                short_call = center + 5
                long_call = short_call + wing_width
            else:  # IRON_BUTTERFLY
                wing_width = 10
                short_put = center
                long_put = center - wing_width
                short_call = center
                long_call = center + wing_width
            
            return {
                'center_strike': float(center),
                'long_put': float(long_put),
                'short_put': float(short_put),
                'short_call': float(short_call),
                'long_call': float(long_call),
                'dte': dte,
                'contracts': 1
            }
        
        elif strategy in ['LONG_CALL', 'LONG_PUT']:
            strike = historical_data['strike'].median()
            dte = int(historical_data['dte'].median())
            
            if np.isnan(strike):
                if strategy == 'LONG_CALL':
                    strike = round(current_price * 1.02 / 5) * 5  # Slightly OTM
                else:
                    strike = round(current_price * 0.98 / 5) * 5  # Slightly OTM
                dte = 30
            
            return {
                'strike': float(strike),
                'dte': dte,
                'contracts': 2
            }
        
        elif strategy in ['LONG_STRADDLE', 'LONG_STRANGLE']:
            dte = int(historical_data['dte'].median())
            
            if np.isnan(dte):
                dte = 21
            
            if strategy == 'LONG_STRADDLE':
                strike = round(current_price / 5) * 5  # ATM
                return {
                    'strike': float(strike),
                    'dte': dte,
                    'contracts': 1
                }
            else:  # LONG_STRANGLE
                call_strike = round(current_price * 1.05 / 5) * 5  # 5% OTM
                put_strike = round(current_price * 0.95 / 5) * 5   # 5% OTM
                return {
                    'call_strike': float(call_strike),
                    'put_strike': float(put_strike),
                    'dte': dte,
                    'contracts': 1
                }
        
        elif strategy in ['CALENDAR_SPREAD', 'DIAGONAL_SPREAD']:
            strike = historical_data['strike'].median()
            near_dte = int(historical_data['near_dte'].median())
            far_dte = int(historical_data['far_dte'].median())
            
            if np.isnan(strike):
                strike = round(current_price / 5) * 5
                near_dte = 7
                far_dte = 30
            
            return {
                'strike': float(strike),
                'near_dte': near_dte,
                'far_dte': far_dte,
                'contracts': 1
            }
        
        else:
            return self._default_parameters(strategy, current_price, 50)
    
    def _default_parameters(self, strategy, current_price, iv_rank):
        """Generate default parameters when no historical data available"""
        
        if strategy in ['BULL_CALL_SPREAD', 'BEAR_PUT_SPREAD']:
            if strategy == 'BULL_CALL_SPREAD':
                long_strike = round(current_price * 0.98 / 5) * 5
                short_strike = long_strike + 10
            else:
                short_strike = round(current_price * 1.02 / 5) * 5
                long_strike = short_strike - 10
            
            return {
                'long_strike': float(long_strike),
                'short_strike': float(short_strike),
                'dte': 21,
                'contracts': 1
            }
        
        elif strategy in ['IRON_CONDOR', 'IRON_BUTTERFLY']:
            center = round(current_price / 5) * 5
            
            if strategy == 'IRON_CONDOR':
                return {
                    'center_strike': float(center),
                    'long_put': float(center - 15),
                    'short_put': float(center - 5),
                    'short_call': float(center + 5),
                    'long_call': float(center + 15),
                    'dte': 30,
                    'contracts': 1
                }
            else:
                return {
                    'center_strike': float(center),
                    'long_put': float(center - 10),
                    'short_put': float(center),
                    'short_call': float(center),
                    'long_call': float(center + 10),
                    'dte': 30,
                    'contracts': 1
                }
        
        elif strategy in ['LONG_CALL', 'LONG_PUT']:
            if strategy == 'LONG_CALL':
                strike = round(current_price * 1.02 / 5) * 5
            else:
                strike = round(current_price * 0.98 / 5) * 5
            
            return {
                'strike': float(strike),
                'dte': 30,
                'contracts': 2
            }
        
        elif strategy == 'LONG_STRADDLE':
            return {
                'strike': float(round(current_price / 5) * 5),
                'dte': 21,
                'contracts': 1
            }
        
        elif strategy == 'LONG_STRANGLE':
            return {
                'call_strike': float(round(current_price * 1.05 / 5) * 5),
                'put_strike': float(round(current_price * 0.95 / 5) * 5),
                'dte': 21,
                'contracts': 1
            }
        
        else:  # CALENDAR_SPREAD, DIAGONAL_SPREAD
            return {
                'strike': float(round(current_price / 5) * 5),
                'near_dte': 7,
                'far_dte': 30,
                'contracts': 1
            }
    
    def predict(self, date=None):
        """Complete two-stage prediction"""
        # Load market data
        market_data = self.load_market_data(date)
        
        if market_data is None:
            return None
        
        # Stage 1: Predict strategy
        prediction = self.predict_strategy(market_data)
        
        # Stage 2: Generate parameters
        parameters = self.generate_parameters(prediction['strategy'], market_data)
        
        # Combine results
        result = {
            'date': market_data['date'].iloc[0].strftime('%Y-%m-%d'),
            'prediction': prediction,
            'parameters': parameters,
            'market_conditions': {
                'current_price': float(market_data['current_price'].iloc[0]),
                'iv_rank': float(market_data['iv_rank'].iloc[0]),
                'adx': float(market_data['adx_14'].iloc[0]),
                'rsi': float(market_data['rsi_14'].iloc[0]),
                'trend_regime': int(market_data['trend_regime'].iloc[0]),
                'volatility_regime': int(market_data['volatility_regime'].iloc[0])
            }
        }
        
        # Summary
        print("=" * 80)
        print("PREDICTION SUMMARY")
        print("=" * 80)
        print()
        print(f"Date: {result['date']}")
        print(f"Strategy: {prediction['strategy']}")
        print(f"Confidence: {prediction['confidence']:.1%}")
        print()
        print("Parameters:")
        for key, value in parameters.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        print()
        print("✅ Prediction complete!")
        print()
        
        return result


def main():
    """Main prediction workflow"""
    parser = argparse.ArgumentParser(description='Predict optimal options strategy')
    parser.add_argument('--date', type=str, help='Date to predict (YYYY-MM-DD)')
    parser.add_argument('--live', action='store_true', help='Use most recent data')
    parser.add_argument('--save', type=str, help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = StrategyPredictor()
    
    # Make prediction
    if args.live:
        result = predictor.predict()
    else:
        result = predictor.predict(args.date)
    
    # Save results if requested
    if result and args.save:
        with open(args.save, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.save}")


if __name__ == "__main__":
    main()
