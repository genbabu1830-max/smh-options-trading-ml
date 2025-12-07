"""
Feature Extractor - Converts Raw Market Data to Model Features
==============================================================

This module takes raw inputs (option chain, price history, market data)
and converts them into the 84 features required by the ML model.

Usage:
    from scripts.utils.feature_extractor import FeatureExtractor
    
    extractor = FeatureExtractor()
    features = extractor.extract_features(
        option_chain=option_chain_df,
        price_history=price_history_df,
        current_date='2024-12-05'
    )
    
    # features is now a dict with 84 features ready for model input
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class FeatureExtractor:
    """
    Extracts 84 model features from raw market data.
    
    Input Requirements:
    - option_chain: DataFrame with columns [strike, type, expiration, dte, bid, ask, 
                    volume, open_interest, iv, delta, gamma, theta, vega]
    - price_history: DataFrame with columns [date, open, high, low, close, volume]
                     (minimum 200 days for sma_200)
    - spy_history: DataFrame with SPY data (optional)
    - vix_history: DataFrame with VIX data (optional)
    
    Output:
    - Dictionary with 84 features matching models/feature_names_clean.json
    """
    
    def __init__(self):
        self.required_features = self._load_feature_names()
    
    def _load_feature_names(self):
        """Load the exact feature names from the trained model."""
        import json
        try:
            with open('models/feature_names_clean.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback to hardcoded list if file not found
            return self._get_default_feature_names()

    
    def _get_default_feature_names(self):
        """Fallback feature names if JSON file not available."""
        return [
            "current_price", "return_1d", "return_3d", "return_5d", "return_10d",
            "return_20d", "return_50d", "rsi_14", "macd", "macd_signal",
            "macd_histogram", "adx_14", "atr_14", "sma_5", "sma_10", "sma_20",
            "sma_50", "sma_200", "price_vs_sma_5", "price_vs_sma_10",
            "price_vs_sma_20", "price_vs_sma_50", "price_vs_sma_200",
            "sma_alignment", "bb_upper", "bb_middle", "bb_lower", "bb_position",
            "volume_20d_avg", "volume_vs_avg", "hv_20d", "iv_atm", "iv_rank",
            "iv_percentile", "hv_iv_ratio", "resistance_level", "support_level",
            "distance_to_resistance", "distance_to_support", "position_in_range",
            "spy_return_1d", "vix_level", "vix_change", "trend_regime",
            "volatility_regime", "volume_regime", "put_call_volume_ratio",
            "put_call_oi_ratio", "total_option_volume", "total_open_interest",
            "atm_delta_call", "atm_delta_put", "atm_gamma", "atm_theta",
            "atm_vega", "max_pain_strike", "distance_to_max_pain", "obv",
            "stochastic_k", "stochastic_d", "cci", "williams_r", "mfi",
            "iv_skew", "iv_term_structure", "vix_vs_ma20", "volatility_trend",
            "parkinson_vol", "garman_klass_vol", "vol_of_vol", "gamma_exposure",
            "delta_exposure", "unusual_activity", "options_flow_sentiment",
            "resistance_2", "support_2", "range_width", "days_in_range",
            "breakout_probability", "spy_correlation", "spy_return_5d",
            "smh_vs_spy", "combined_state", "days_since_regime_change"
        ]
    
    def extract_features(
        self,
        option_chain: pd.DataFrame,
        price_history: pd.DataFrame,
        current_date: str,
        spy_history: Optional[pd.DataFrame] = None,
        vix_history: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        Extract all 84 features from raw market data.
        
        Args:
            option_chain: Current option chain data
            price_history: Historical price data (min 200 days)
            current_date: Date for prediction (YYYY-MM-DD)
            spy_history: SPY historical data (optional)
            vix_history: VIX historical data (optional)
        
        Returns:
            Dictionary with 84 features
        """
        features = {}
        
        # Validate inputs
        self._validate_inputs(option_chain, price_history, current_date)
        
        # Get current price data
        current_idx = price_history[price_history['date'] == current_date].index
        if len(current_idx) == 0:
            raise ValueError(f"Date {current_date} not found in price_history")
        current_idx = current_idx[0]
        
        # Extract features by category
        features.update(self._extract_price_features(price_history, current_idx))
        features.update(self._extract_technical_indicators(price_history, current_idx))
        features.update(self._extract_volatility_features(option_chain, price_history, current_idx))
        features.update(self._extract_options_metrics(option_chain, price_history.iloc[current_idx]['close']))
        features.update(self._extract_support_resistance(price_history, current_idx))
        features.update(self._extract_market_context(spy_history, vix_history, current_idx))
        features.update(self._extract_regime_classification(features))
        
        # Ensure all 84 features present
        self._validate_output(features)
        
        return features

    
    def _validate_inputs(self, option_chain, price_history, current_date):
        """Validate input data quality."""
        # Check option chain columns
        required_option_cols = ['strike', 'type', 'expiration', 'dte', 'bid', 'ask',
                                'volume', 'open_interest', 'iv', 'delta', 'gamma', 
                                'theta', 'vega']
        missing_cols = set(required_option_cols) - set(option_chain.columns)
        if missing_cols:
            raise ValueError(f"Option chain missing columns: {missing_cols}")
        
        # Check price history columns
        required_price_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = set(required_price_cols) - set(price_history.columns)
        if missing_cols:
            raise ValueError(f"Price history missing columns: {missing_cols}")
        
        # Check sufficient history
        if len(price_history) < 200:
            warnings.warn(f"Price history has only {len(price_history)} days. "
                         f"Recommend 200+ days for sma_200 calculation.")
    
    def _validate_output(self, features):
        """Ensure all 84 features are present."""
        missing = set(self.required_features) - set(features.keys())
        if missing:
            raise ValueError(f"Missing features: {missing}")
        
        extra = set(features.keys()) - set(self.required_features)
        if extra:
            warnings.warn(f"Extra features will be ignored: {extra}")
        
        # Check for NaN values
        nan_features = [k for k, v in features.items() if pd.isna(v)]
        if nan_features:
            raise ValueError(f"Features contain NaN values: {nan_features}")
    
    def _extract_price_features(self, df, current_idx):
        """Extract price-based features (22 features)."""
        features = {}
        
        # Current price
        features['current_price'] = df.iloc[current_idx]['close']
        
        # Returns
        for days in [1, 3, 5, 10, 20, 50]:
            if current_idx >= days:
                past_price = df.iloc[current_idx - days]['close']
                features[f'return_{days}d'] = (features['current_price'] - past_price) / past_price
            else:
                features[f'return_{days}d'] = 0.0
        
        # Moving averages
        for period in [5, 10, 20, 50, 200]:
            if current_idx >= period - 1:
                features[f'sma_{period}'] = df.iloc[current_idx - period + 1:current_idx + 1]['close'].mean()
            else:
                features[f'sma_{period}'] = features['current_price']
        
        # Price vs SMAs
        for period in [5, 10, 20, 50, 200]:
            sma_key = f'sma_{period}'
            if features[sma_key] > 0:
                features[f'price_vs_sma_{period}'] = (features['current_price'] - features[sma_key]) / features[sma_key]
            else:
                features[f'price_vs_sma_{period}'] = 0.0
        
        # SMA alignment (bullish if all SMAs in order)
        features['sma_alignment'] = 1 if (
            features['sma_5'] > features['sma_10'] > features['sma_20'] > 
            features['sma_50'] > features['sma_200']
        ) else 0
        
        # Bollinger Bands
        if current_idx >= 19:
            closes = df.iloc[current_idx - 19:current_idx + 1]['close']
            features['bb_middle'] = closes.mean()
            bb_std = closes.std()
            features['bb_upper'] = features['bb_middle'] + (2 * bb_std)
            features['bb_lower'] = features['bb_middle'] - (2 * bb_std)
            
            if features['bb_upper'] > features['bb_lower']:
                features['bb_position'] = (features['current_price'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
            else:
                features['bb_position'] = 0.5
        else:
            features['bb_middle'] = features['current_price']
            features['bb_upper'] = features['current_price'] * 1.05
            features['bb_lower'] = features['current_price'] * 0.95
            features['bb_position'] = 0.5
        
        return features

    
    def _extract_technical_indicators(self, df, current_idx):
        """Extract technical indicators (14 features)."""
        features = {}
        
        # RSI (14-period)
        if current_idx >= 14:
            closes = df.iloc[current_idx - 14:current_idx + 1]['close'].values
            deltas = np.diff(closes)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss == 0:
                features['rsi_14'] = 100.0
            else:
                rs = avg_gain / avg_loss
                features['rsi_14'] = 100 - (100 / (1 + rs))
        else:
            features['rsi_14'] = 50.0
        
        # MACD
        if current_idx >= 26:
            closes = df.iloc[:current_idx + 1]['close']
            ema_12 = closes.ewm(span=12, adjust=False).mean().iloc[-1]
            ema_26 = closes.ewm(span=26, adjust=False).mean().iloc[-1]
            features['macd'] = ema_12 - ema_26
            
            # MACD signal line (9-period EMA of MACD)
            macd_line = closes.ewm(span=12, adjust=False).mean() - closes.ewm(span=26, adjust=False).mean()
            features['macd_signal'] = macd_line.ewm(span=9, adjust=False).mean().iloc[-1]
            features['macd_histogram'] = features['macd'] - features['macd_signal']
        else:
            features['macd'] = 0.0
            features['macd_signal'] = 0.0
            features['macd_histogram'] = 0.0
        
        # ADX (14-period)
        if current_idx >= 14:
            high = df.iloc[current_idx - 14:current_idx + 1]['high'].values
            low = df.iloc[current_idx - 14:current_idx + 1]['low'].values
            close = df.iloc[current_idx - 14:current_idx + 1]['close'].values
            
            # Calculate +DM and -DM
            high_diff = np.diff(high)
            low_diff = -np.diff(low)
            
            plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
            minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
            
            # Calculate TR
            tr1 = high[1:] - low[1:]
            tr2 = np.abs(high[1:] - close[:-1])
            tr3 = np.abs(low[1:] - close[:-1])
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # Calculate smoothed values
            atr = np.mean(tr)
            plus_di = 100 * np.mean(plus_dm) / atr if atr > 0 else 0
            minus_di = 100 * np.mean(minus_dm) / atr if atr > 0 else 0
            
            # Calculate ADX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0
            features['adx_14'] = dx
        else:
            features['adx_14'] = 20.0
        
        # ATR (14-period)
        if current_idx >= 14:
            high = df.iloc[current_idx - 14:current_idx + 1]['high'].values
            low = df.iloc[current_idx - 14:current_idx + 1]['low'].values
            close = df.iloc[current_idx - 14:current_idx + 1]['close'].values
            
            tr1 = high[1:] - low[1:]
            tr2 = np.abs(high[1:] - close[:-1])
            tr3 = np.abs(low[1:] - close[:-1])
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            features['atr_14'] = np.mean(tr)
        else:
            features['atr_14'] = df.iloc[current_idx]['close'] * 0.02
        
        # Volume metrics
        if current_idx >= 19:
            features['volume_20d_avg'] = df.iloc[current_idx - 19:current_idx + 1]['volume'].mean()
            features['volume_vs_avg'] = df.iloc[current_idx]['volume'] / features['volume_20d_avg']
        else:
            features['volume_20d_avg'] = df.iloc[current_idx]['volume']
            features['volume_vs_avg'] = 1.0
        
        # OBV (On-Balance Volume)
        if current_idx >= 1:
            obv = 0
            for i in range(1, current_idx + 1):
                if df.iloc[i]['close'] > df.iloc[i-1]['close']:
                    obv += df.iloc[i]['volume']
                elif df.iloc[i]['close'] < df.iloc[i-1]['close']:
                    obv -= df.iloc[i]['volume']
            features['obv'] = obv
        else:
            features['obv'] = 0.0
        
        # Stochastic Oscillator (14-period)
        if current_idx >= 14:
            high_14 = df.iloc[current_idx - 13:current_idx + 1]['high'].max()
            low_14 = df.iloc[current_idx - 13:current_idx + 1]['low'].min()
            close_current = df.iloc[current_idx]['close']
            
            if high_14 > low_14:
                features['stochastic_k'] = 100 * (close_current - low_14) / (high_14 - low_14)
            else:
                features['stochastic_k'] = 50.0
            
            # %D is 3-period SMA of %K
            if current_idx >= 16:
                k_values = []
                for i in range(current_idx - 2, current_idx + 1):
                    h = df.iloc[i - 13:i + 1]['high'].max()
                    l = df.iloc[i - 13:i + 1]['low'].min()
                    c = df.iloc[i]['close']
                    k_values.append(100 * (c - l) / (h - l) if h > l else 50.0)
                features['stochastic_d'] = np.mean(k_values)
            else:
                features['stochastic_d'] = features['stochastic_k']
        else:
            features['stochastic_k'] = 50.0
            features['stochastic_d'] = 50.0
        
        # CCI (Commodity Channel Index, 20-period)
        if current_idx >= 20:
            tp = (df.iloc[current_idx - 19:current_idx + 1]['high'] + 
                  df.iloc[current_idx - 19:current_idx + 1]['low'] + 
                  df.iloc[current_idx - 19:current_idx + 1]['close']) / 3
            sma_tp = tp.mean()
            mad = np.mean(np.abs(tp - sma_tp))
            features['cci'] = (tp.iloc[-1] - sma_tp) / (0.015 * mad) if mad > 0 else 0.0
        else:
            features['cci'] = 0.0
        
        # Williams %R (14-period)
        if current_idx >= 14:
            high_14 = df.iloc[current_idx - 13:current_idx + 1]['high'].max()
            low_14 = df.iloc[current_idx - 13:current_idx + 1]['low'].min()
            close_current = df.iloc[current_idx]['close']
            
            if high_14 > low_14:
                features['williams_r'] = -100 * (high_14 - close_current) / (high_14 - low_14)
            else:
                features['williams_r'] = -50.0
        else:
            features['williams_r'] = -50.0
        
        # MFI (Money Flow Index, 14-period)
        if current_idx >= 14:
            tp = (df.iloc[current_idx - 14:current_idx + 1]['high'] + 
                  df.iloc[current_idx - 14:current_idx + 1]['low'] + 
                  df.iloc[current_idx - 14:current_idx + 1]['close']) / 3
            mf = tp * df.iloc[current_idx - 14:current_idx + 1]['volume']
            
            positive_mf = 0
            negative_mf = 0
            for i in range(1, len(tp)):
                if tp.iloc[i] > tp.iloc[i-1]:
                    positive_mf += mf.iloc[i]
                elif tp.iloc[i] < tp.iloc[i-1]:
                    negative_mf += mf.iloc[i]
            
            if negative_mf == 0:
                features['mfi'] = 100.0
            else:
                mfr = positive_mf / negative_mf
                features['mfi'] = 100 - (100 / (1 + mfr))
        else:
            features['mfi'] = 50.0
        
        return features

    
    def _extract_volatility_features(self, option_chain, price_history, current_idx):
        """Extract volatility features (14 features)."""
        features = {}
        current_price = price_history.iloc[current_idx]['close']
        
        # Historical Volatility (20-day)
        if current_idx >= 20:
            returns = price_history.iloc[current_idx - 19:current_idx + 1]['close'].pct_change().dropna()
            features['hv_20d'] = returns.std() * np.sqrt(252)
        else:
            features['hv_20d'] = 0.25
        
        # ATM Implied Volatility
        atm_options = option_chain[
            (option_chain['strike'] >= current_price * 0.98) &
            (option_chain['strike'] <= current_price * 1.02)
        ]
        if len(atm_options) > 0:
            features['iv_atm'] = atm_options['iv'].mean()
        else:
            features['iv_atm'] = 0.25
        
        # IV Rank (requires 252-day IV history - calculate from option chain if available)
        # For now, use a simplified version based on current IV
        features['iv_rank'] = min(100, max(0, (features['iv_atm'] - 0.15) / (0.50 - 0.15) * 100))
        
        # IV Percentile (simplified)
        features['iv_percentile'] = features['iv_rank']
        
        # HV/IV Ratio
        if features['iv_atm'] > 0:
            features['hv_iv_ratio'] = features['hv_20d'] / features['iv_atm']
        else:
            features['hv_iv_ratio'] = 1.0
        
        # IV Skew (OTM Put IV - OTM Call IV)
        otm_puts = option_chain[
            (option_chain['type'] == 'put') &
            (option_chain['strike'] < current_price * 0.95) &
            (option_chain['strike'] > current_price * 0.85)
        ]
        otm_calls = option_chain[
            (option_chain['type'] == 'call') &
            (option_chain['strike'] > current_price * 1.05) &
            (option_chain['strike'] < current_price * 1.15)
        ]
        
        if len(otm_puts) > 0 and len(otm_calls) > 0:
            features['iv_skew'] = otm_puts['iv'].mean() - otm_calls['iv'].mean()
        else:
            features['iv_skew'] = 0.0
        
        # IV Term Structure (near-term vs far-term)
        near_term = option_chain[(option_chain['dte'] >= 7) & (option_chain['dte'] <= 21)]
        far_term = option_chain[(option_chain['dte'] >= 45) & (option_chain['dte'] <= 90)]
        
        if len(near_term) > 0 and len(far_term) > 0:
            features['iv_term_structure'] = near_term['iv'].mean() - far_term['iv'].mean()
        else:
            features['iv_term_structure'] = 0.0
        
        # VIX metrics (placeholder - would need actual VIX data)
        features['vix_level'] = 16.0  # Default
        features['vix_change'] = 0.0
        features['vix_vs_ma20'] = 1.0
        
        # Volatility trend
        features['volatility_trend'] = 1 if features['hv_20d'] > features['iv_atm'] else 0
        
        # Parkinson Volatility (high-low estimator)
        if current_idx >= 20:
            high = price_history.iloc[current_idx - 19:current_idx + 1]['high']
            low = price_history.iloc[current_idx - 19:current_idx + 1]['low']
            hl_ratio = np.log(high / low)
            features['parkinson_vol'] = np.sqrt(np.mean(hl_ratio ** 2) / (4 * np.log(2))) * np.sqrt(252)
        else:
            features['parkinson_vol'] = features['hv_20d']
        
        # Garman-Klass Volatility (OHLC estimator)
        if current_idx >= 20:
            high = price_history.iloc[current_idx - 19:current_idx + 1]['high']
            low = price_history.iloc[current_idx - 19:current_idx + 1]['low']
            close = price_history.iloc[current_idx - 19:current_idx + 1]['close']
            open_price = price_history.iloc[current_idx - 19:current_idx + 1]['open']
            
            hl = np.log(high / low) ** 2
            co = np.log(close / open_price) ** 2
            features['garman_klass_vol'] = np.sqrt(np.mean(0.5 * hl - (2 * np.log(2) - 1) * co)) * np.sqrt(252)
        else:
            features['garman_klass_vol'] = features['hv_20d']
        
        # Volatility of Volatility
        if current_idx >= 40:
            # Calculate rolling 20-day HV for last 20 periods
            hvs = []
            for i in range(current_idx - 19, current_idx + 1):
                if i >= 20:
                    returns = price_history.iloc[i - 19:i + 1]['close'].pct_change().dropna()
                    hvs.append(returns.std() * np.sqrt(252))
            if len(hvs) > 1:
                features['vol_of_vol'] = np.std(hvs)
            else:
                features['vol_of_vol'] = 0.05
        else:
            features['vol_of_vol'] = 0.05
        
        return features

    
    def _extract_options_metrics(self, option_chain, current_price):
        """Extract options market metrics (15 features)."""
        features = {}
        
        # Put/Call Ratios
        puts = option_chain[option_chain['type'] == 'put']
        calls = option_chain[option_chain['type'] == 'call']
        
        put_volume = puts['volume'].sum()
        call_volume = calls['volume'].sum()
        features['put_call_volume_ratio'] = put_volume / call_volume if call_volume > 0 else 1.0
        
        put_oi = puts['open_interest'].sum()
        call_oi = calls['open_interest'].sum()
        features['put_call_oi_ratio'] = put_oi / call_oi if call_oi > 0 else 1.0
        
        # Total metrics
        features['total_option_volume'] = option_chain['volume'].sum()
        features['total_open_interest'] = option_chain['open_interest'].sum()
        
        # ATM Greeks (options within 2% of current price)
        atm_options = option_chain[
            (option_chain['strike'] >= current_price * 0.98) &
            (option_chain['strike'] <= current_price * 1.02)
        ]
        
        atm_calls = atm_options[atm_options['type'] == 'call']
        atm_puts = atm_options[atm_options['type'] == 'put']
        
        features['atm_delta_call'] = atm_calls['delta'].mean() if len(atm_calls) > 0 else 0.5
        features['atm_delta_put'] = atm_puts['delta'].mean() if len(atm_puts) > 0 else -0.5
        features['atm_gamma'] = atm_options['gamma'].mean() if len(atm_options) > 0 else 0.05
        features['atm_theta'] = atm_options['theta'].mean() if len(atm_options) > 0 else -0.05
        features['atm_vega'] = atm_options['vega'].mean() if len(atm_options) > 0 else 0.10
        
        # Max Pain (strike where most options expire worthless)
        strikes = option_chain['strike'].unique()
        max_pain = current_price
        min_loss = float('inf')
        
        for strike in strikes:
            # Calculate total loss for option writers at this strike
            call_loss = calls[calls['strike'] <= strike].apply(
                lambda x: max(0, strike - x['strike']) * x['open_interest'], axis=1
            ).sum()
            put_loss = puts[puts['strike'] >= strike].apply(
                lambda x: max(0, x['strike'] - strike) * x['open_interest'], axis=1
            ).sum()
            total_loss = call_loss + put_loss
            
            if total_loss < min_loss:
                min_loss = total_loss
                max_pain = strike
        
        features['max_pain_strike'] = max_pain
        features['distance_to_max_pain'] = (current_price - max_pain) / current_price
        
        # Gamma Exposure (aggregate gamma weighted by OI)
        features['gamma_exposure'] = (option_chain['gamma'] * option_chain['open_interest']).sum() / 1000
        
        # Delta Exposure (aggregate delta weighted by OI)
        features['delta_exposure'] = (option_chain['delta'] * option_chain['open_interest']).sum() / 1000
        
        # Unusual Activity (volume > 2x average)
        avg_volume = option_chain['volume'].mean()
        features['unusual_activity'] = 1 if features['total_option_volume'] > 2 * avg_volume * len(option_chain) else 0
        
        # Options Flow Sentiment
        if features['total_option_volume'] > 0:
            features['options_flow_sentiment'] = (call_volume - put_volume) / features['total_option_volume']
        else:
            features['options_flow_sentiment'] = 0.0
        
        return features

    
    def _extract_support_resistance(self, price_history, current_idx):
        """Extract support/resistance features (10 features)."""
        features = {}
        current_price = price_history.iloc[current_idx]['close']
        
        # Look back 60 days for support/resistance
        lookback = min(60, current_idx + 1)
        recent_data = price_history.iloc[max(0, current_idx - lookback + 1):current_idx + 1]
        
        # Find resistance levels (recent highs)
        highs = recent_data.nlargest(5, 'high')['high'].values
        features['resistance_level'] = highs[0] if len(highs) > 0 else current_price * 1.05
        features['resistance_2'] = highs[1] if len(highs) > 1 else features['resistance_level'] * 1.02
        
        # Find support levels (recent lows)
        lows = recent_data.nsmallest(5, 'low')['low'].values
        features['support_level'] = lows[0] if len(lows) > 0 else current_price * 0.95
        features['support_2'] = lows[1] if len(lows) > 1 else features['support_level'] * 0.98
        
        # Distance calculations
        features['distance_to_resistance'] = (features['resistance_level'] - current_price) / current_price
        features['distance_to_support'] = (current_price - features['support_level']) / current_price
        
        # Position in range
        range_size = features['resistance_level'] - features['support_level']
        if range_size > 0:
            features['position_in_range'] = (current_price - features['support_level']) / range_size
        else:
            features['position_in_range'] = 0.5
        
        # Range width
        features['range_width'] = range_size / current_price
        
        # Days in range (days since breakout)
        days_in_range = 0
        for i in range(current_idx, max(0, current_idx - 60), -1):
            price = price_history.iloc[i]['close']
            if features['support_level'] <= price <= features['resistance_level']:
                days_in_range += 1
            else:
                break
        features['days_in_range'] = days_in_range
        
        # Breakout probability (simplified heuristic)
        # Higher when price near resistance/support and volatility increasing
        distance_factor = min(features['distance_to_resistance'], features['distance_to_support'])
        features['breakout_probability'] = min(1.0, (1 - distance_factor * 10) * 0.5)
        
        return features
    
    def _extract_market_context(self, spy_history, vix_history, current_idx):
        """Extract market context features (10 features)."""
        features = {}
        
        # SPY metrics (if available)
        if spy_history is not None and len(spy_history) > current_idx:
            spy_current = spy_history.iloc[current_idx]['close']
            
            if current_idx >= 1:
                spy_prev = spy_history.iloc[current_idx - 1]['close']
                features['spy_return_1d'] = (spy_current - spy_prev) / spy_prev
            else:
                features['spy_return_1d'] = 0.0
            
            if current_idx >= 5:
                spy_5d_ago = spy_history.iloc[current_idx - 5]['close']
                features['spy_return_5d'] = (spy_current - spy_5d_ago) / spy_5d_ago
            else:
                features['spy_return_5d'] = 0.0
            
            # SPY correlation (30-day)
            # This would require SMH returns - simplified for now
            features['spy_correlation'] = 0.80  # Default high correlation
            
            # Relative performance (would need SMH return)
            features['smh_vs_spy'] = 0.0  # Placeholder
        else:
            features['spy_return_1d'] = 0.0
            features['spy_return_5d'] = 0.0
            features['spy_correlation'] = 0.80
            features['smh_vs_spy'] = 0.0
        
        # VIX metrics (if available)
        if vix_history is not None and len(vix_history) > current_idx:
            features['vix_level'] = vix_history.iloc[current_idx]['close']
            
            if current_idx >= 1:
                vix_prev = vix_history.iloc[current_idx - 1]['close']
                features['vix_change'] = features['vix_level'] - vix_prev
            else:
                features['vix_change'] = 0.0
            
            if current_idx >= 20:
                vix_ma20 = vix_history.iloc[current_idx - 19:current_idx + 1]['close'].mean()
                features['vix_vs_ma20'] = features['vix_level'] / vix_ma20 if vix_ma20 > 0 else 1.0
            else:
                features['vix_vs_ma20'] = 1.0
        else:
            features['vix_level'] = 16.0
            features['vix_change'] = 0.0
            features['vix_vs_ma20'] = 1.0
        
        return features

    
    def _extract_regime_classification(self, features):
        """Extract regime classification features (5 features)."""
        regime_features = {}
        
        # Trend Regime (0=strong_down, 1=weak_down, 2=ranging, 3=weak_up, 4=strong_up)
        adx = features.get('adx_14', 20)
        macd_hist = features.get('macd_histogram', 0)
        price_vs_sma50 = features.get('price_vs_sma_50', 0)
        
        if adx > 30 and macd_hist > 0 and price_vs_sma50 > 0.02:
            regime_features['trend_regime'] = 4  # strong_up
        elif adx > 25 and price_vs_sma50 > 0:
            regime_features['trend_regime'] = 3  # weak_up
        elif adx < 20:
            regime_features['trend_regime'] = 2  # ranging
        elif adx > 25 and price_vs_sma50 < 0:
            regime_features['trend_regime'] = 1  # weak_down
        else:
            regime_features['trend_regime'] = 0  # strong_down
        
        # Volatility Regime (0=very_low, 1=low, 2=normal, 3=elevated, 4=very_high)
        iv_rank = features.get('iv_rank', 50)
        
        if iv_rank > 75:
            regime_features['volatility_regime'] = 4
        elif iv_rank > 60:
            regime_features['volatility_regime'] = 3
        elif iv_rank > 40:
            regime_features['volatility_regime'] = 2
        elif iv_rank > 25:
            regime_features['volatility_regime'] = 1
        else:
            regime_features['volatility_regime'] = 0
        
        # Volume Regime (0=low, 1=normal, 2=high)
        volume_vs_avg = features.get('volume_vs_avg', 1.0)
        
        if volume_vs_avg > 1.5:
            regime_features['volume_regime'] = 2
        elif volume_vs_avg > 0.8:
            regime_features['volume_regime'] = 1
        else:
            regime_features['volume_regime'] = 0
        
        # Combined State (encoded combination of regimes)
        regime_features['combined_state'] = (
            regime_features['trend_regime'] * 15 +
            regime_features['volatility_regime'] * 3 +
            regime_features['volume_regime']
        )
        
        # Days Since Regime Change (simplified - would need historical tracking)
        regime_features['days_since_regime_change'] = 5  # Default placeholder
        
        return regime_features
    
    def get_feature_array(self, features: Dict[str, float]) -> np.ndarray:
        """
        Convert feature dictionary to ordered numpy array for model input.
        
        Args:
            features: Dictionary with 84 features
        
        Returns:
            Numpy array with features in correct order
        """
        return np.array([features[name] for name in self.required_features])
    
    def get_feature_dataframe(self, features: Dict[str, float]) -> pd.DataFrame:
        """
        Convert feature dictionary to pandas DataFrame for model input.
        
        Args:
            features: Dictionary with 84 features
        
        Returns:
            DataFrame with one row and 84 columns
        """
        return pd.DataFrame([features], columns=self.required_features)


# Example usage
if __name__ == "__main__":
    print("Feature Extractor Module")
    print("=" * 60)
    print("\nThis module converts raw market data into 84 model features.")
    print("\nUsage:")
    print("  from scripts.utils.feature_extractor import FeatureExtractor")
    print("  extractor = FeatureExtractor()")
    print("  features = extractor.extract_features(option_chain, price_history, date)")
    print("\nFeatures extracted: 84")
    print("  - Price Features: 22")
    print("  - Technical Indicators: 14")
    print("  - Volatility Features: 14")
    print("  - Options Metrics: 15")
    print("  - Support/Resistance: 10")
    print("  - Market Context: 4")
    print("  - Regime Classification: 5")
