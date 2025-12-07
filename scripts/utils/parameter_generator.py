"""
Enhanced Parameter Generator with Risk Management
=================================================

Generates optimal trade parameters for each strategy using:
- IV-adaptive strike selection
- Delta-based targeting
- Trend-strength adjustments
- Position sizing with risk management
- Portfolio risk controls

Author: Options Trading System
Date: December 6, 2024
Version: 2.0 (Enhanced)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


class RiskManager:
    """
    Manages position sizing and risk controls.
    """
    
    def __init__(self, account_size: float = 10000, risk_per_trade: float = 0.02,
                 max_contracts: int = 10):
        """
        Initialize risk manager.
        
        Args:
            account_size: Total account value
            risk_per_trade: Maximum risk per trade (0.02 = 2%)
            max_contracts: Maximum contracts per position
        """
        self.account_size = account_size
        self.risk_per_trade = risk_per_trade
        self.max_contracts = max_contracts
        self.max_risk_amount = account_size * risk_per_trade
    
    def calculate_position_size(self, max_loss_per_contract: float) -> int:
        """
        Calculate optimal number of contracts based on risk.
        
        Args:
            max_loss_per_contract: Maximum loss per contract
        
        Returns:
            Number of contracts (1 to max_contracts)
        """
        if max_loss_per_contract <= 0:
            return 1
        
        # Calculate contracts based on risk
        contracts = int(self.max_risk_amount / max_loss_per_contract)
        
        # Ensure between 1 and max
        return max(1, min(contracts, self.max_contracts))
    
    def validate_trade(self, max_loss: float, max_profit: float) -> Dict:
        """
        Validate if trade meets risk criteria.
        
        Args:
            max_loss: Maximum loss for position
            max_profit: Maximum profit for position
        
        Returns:
            Dict with validation results
        """
        risk_reward_ratio = max_profit / abs(max_loss) if max_loss != 0 else 0
        risk_pct = abs(max_loss) / self.account_size
        
        return {
            'approved': risk_pct <= self.risk_per_trade and risk_reward_ratio > 0.5,
            'risk_reward_ratio': risk_reward_ratio,
            'risk_percentage': risk_pct,
            'max_risk_amount': self.max_risk_amount,
            'warnings': []
        }


class ParameterGenerator:
    """
    Enhanced parameter generator with sophisticated rules.
    """
    
    def __init__(self, risk_manager: Optional[RiskManager] = None):
        """
        Initialize parameter generator.
        
        Args:
            risk_manager: RiskManager instance (creates default if None)
        """
        self.risk_manager = risk_manager or RiskManager()
    
    def generate(self, strategy: str, option_chain: pd.DataFrame,
                 features: Dict, current_price: float) -> Dict:
        """
        Generate parameters for given strategy.
        
        Args:
            strategy: Strategy name
            option_chain: Available options
            features: Market features (84 features)
            current_price: Current underlying price
        
        Returns:
            Dict with strategy parameters
        """
        # Route to strategy-specific generator
        generators = {
            'LONG_CALL': self._generate_long_call,
            'LONG_PUT': self._generate_long_put,
            'BULL_CALL_SPREAD': self._generate_bull_call_spread,
            'BEAR_PUT_SPREAD': self._generate_bear_put_spread,
            'LONG_STRADDLE': self._generate_long_straddle,
            'LONG_STRANGLE': self._generate_long_strangle,
            'IRON_CONDOR': self._generate_iron_condor,
            'IRON_BUTTERFLY': self._generate_iron_butterfly,
            'CALENDAR_SPREAD': self._generate_calendar_spread,
            'DIAGONAL_SPREAD': self._generate_diagonal_spread
        }
        
        if strategy not in generators:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        return generators[strategy](option_chain, features, current_price)
    
    def _select_optimal_dte(self, option_chain: pd.DataFrame, strategy: str,
                           iv_rank: float, trend_strength: str) -> int:
        """
        Select optimal DTE based on strategy and market conditions.
        
        Args:
            option_chain: Available options
            strategy: Strategy name
            iv_rank: IV rank (0-100)
            trend_strength: Trend strength classification
        
        Returns:
            Optimal DTE
        """
        available_dtes = sorted(option_chain['dte'].unique())
        
        # Strategy-specific DTE preferences
        if strategy in ['IRON_CONDOR', 'IRON_BUTTERFLY']:
            # High IV → shorter DTE (capture theta faster)
            if iv_rank > 70:
                target = 7
            elif iv_rank > 50:
                target = 14
            else:
                target = 21
        
        elif strategy in ['LONG_CALL', 'LONG_PUT']:
            # Low IV → longer DTE (time to develop)
            # Strong trend → longer DTE (ride it)
            if iv_rank < 30 and trend_strength == 'VERY_STRONG':
                target = 45
            elif iv_rank < 40:
                target = 30
            else:
                target = 21
        
        elif strategy in ['BULL_CALL_SPREAD', 'BEAR_PUT_SPREAD']:
            # Moderate DTE for spreads
            if trend_strength == 'VERY_STRONG':
                target = 30
            else:
                target = 21
        
        else:
            # Default
            target = 30
        
        # Find closest available DTE
        return min(available_dtes, key=lambda x: abs(x - target))
    
    def _classify_trend_strength(self, features: Dict) -> str:
        """
        Classify trend strength from features.
        
        Args:
            features: Market features
        
        Returns:
            Trend strength: VERY_STRONG, STRONG, MODERATE, WEAK
        """
        rsi = features.get('rsi_14', 50)
        adx = features.get('adx_14', 20)
        trend_regime = features.get('trend_regime', 2)
        
        if adx > 30 and ((rsi > 65 and trend_regime >= 4) or (rsi < 35 and trend_regime <= 0)):
            return 'VERY_STRONG'
        elif adx > 25 and ((rsi > 60 and trend_regime >= 3) or (rsi < 40 and trend_regime <= 1)):
            return 'STRONG'
        elif adx > 20:
            return 'MODERATE'
        else:
            return 'WEAK'
    
    def _find_strike_by_delta(self, option_chain: pd.DataFrame, target_delta: float,
                              option_type: str, dte: int) -> float:
        """
        Find strike closest to target delta (professional approach).
        
        Args:
            option_chain: Available options
            target_delta: Target delta (e.g., 0.30 for 30 delta)
            option_type: 'call' or 'put'
            dte: Days to expiration
        
        Returns:
            Strike price
        """
        # Filter by type and DTE
        filtered = option_chain[
            (option_chain['type'] == option_type) &
            (option_chain['dte'] == dte)
        ].copy()
        
        if len(filtered) == 0:
            # Fallback to any DTE
            filtered = option_chain[option_chain['type'] == option_type].copy()
        
        if len(filtered) == 0:
            raise ValueError(f"No {option_type} options available")
        
        # Find closest delta
        filtered['delta_diff'] = (filtered['delta'].abs() - abs(target_delta)).abs()
        best = filtered.nsmallest(1, 'delta_diff')
        
        return float(best['strike'].iloc[0])
    
    def _find_strike_by_price(self, option_chain: pd.DataFrame, target_price: float,
                             option_type: str, dte: int) -> float:
        """
        Find strike closest to target price.
        
        Args:
            option_chain: Available options
            target_price: Target strike price
            option_type: 'call' or 'put'
            dte: Days to expiration
        
        Returns:
            Strike price
        """
        # Filter by type and DTE
        filtered = option_chain[
            (option_chain['type'] == option_type) &
            (option_chain['dte'] == dte)
        ].copy()
        
        if len(filtered) == 0:
            filtered = option_chain[option_chain['type'] == option_type].copy()
        
        if len(filtered) == 0:
            raise ValueError(f"No {option_type} options available")
        
        # Find closest strike
        filtered['price_diff'] = (filtered['strike'] - target_price).abs()
        best = filtered.nsmallest(1, 'price_diff')
        
        return float(best['strike'].iloc[0])

    
    def _get_option_cost(self, option_chain: pd.DataFrame, strike: float,
                        option_type: str, dte: int) -> float:
        """
        Get option cost (ask price) for given strike.
        
        Args:
            option_chain: Available options
            strike: Strike price
            option_type: 'call' or 'put'
            dte: Days to expiration
        
        Returns:
            Ask price
        """
        option = option_chain[
            (option_chain['strike'] == strike) &
            (option_chain['type'] == option_type) &
            (option_chain['dte'] == dte)
        ]
        
        if len(option) == 0:
            raise ValueError(f"Option not found: {option_type} ${strike} {dte}DTE")
        
        return float(option['ask'].iloc[0])
    
    def _get_option_bid(self, option_chain: pd.DataFrame, strike: float,
                       option_type: str, dte: int) -> float:
        """
        Get option bid price for given strike.
        
        Args:
            option_chain: Available options
            strike: Strike price
            option_type: 'call' or 'put'
            dte: Days to expiration
        
        Returns:
            Bid price
        """
        option = option_chain[
            (option_chain['strike'] == strike) &
            (option_chain['type'] == option_type) &
            (option_chain['dte'] == dte)
        ]
        
        if len(option) == 0:
            raise ValueError(f"Option not found: {option_type} ${strike} {dte}DTE")
        
        return float(option['bid'].iloc[0])
    
    # ========================================================================
    # STRATEGY-SPECIFIC GENERATORS
    # ========================================================================
    
    def _generate_long_call(self, option_chain: pd.DataFrame, features: Dict,
                           current_price: float) -> Dict:
        """
        Generate parameters for LONG CALL.
        
        Strategy: Buy ATM or slightly OTM call
        Best when: Low IV + Strong uptrend
        """
        iv_rank = features.get('iv_rank', 50)
        trend_strength = self._classify_trend_strength(features)
        
        # Select DTE
        dte = self._select_optimal_dte(option_chain, 'LONG_CALL', iv_rank, trend_strength)
        
        # IV-adaptive strike selection
        if iv_rank < 30:
            # Very low IV → buy ATM (maximize leverage)
            target_delta = 0.50
        elif iv_rank < 40:
            # Low IV → slightly OTM
            target_delta = 0.40
        else:
            # Medium IV → more OTM
            target_delta = 0.30
        
        # Find strike by delta
        strike = self._find_strike_by_delta(option_chain, target_delta, 'call', dte)
        cost = self._get_option_cost(option_chain, strike, 'call', dte)
        
        # Position sizing
        max_loss_per_contract = cost * 100
        contracts = self.risk_manager.calculate_position_size(max_loss_per_contract)
        
        # Calculate metrics
        total_cost = cost * 100 * contracts
        
        return {
            'strategy': 'LONG_CALL',
            'action': 'BUY',
            'option_type': 'CALL',
            'strike': strike,
            'dte': dte,
            'contracts': contracts,
            'cost_per_contract': cost * 100,
            'total_cost': total_cost,
            'max_loss': total_cost,
            'max_profit': 'Unlimited',
            'breakeven': strike + cost,
            'target_delta': target_delta,
            'iv_rank': iv_rank,
            'trend_strength': trend_strength
        }
    
    def _generate_long_put(self, option_chain: pd.DataFrame, features: Dict,
                          current_price: float) -> Dict:
        """
        Generate parameters for LONG PUT.
        
        Strategy: Buy ATM or slightly OTM put
        Best when: Low IV + Strong downtrend
        """
        iv_rank = features.get('iv_rank', 50)
        trend_strength = self._classify_trend_strength(features)
        
        # Select DTE
        dte = self._select_optimal_dte(option_chain, 'LONG_PUT', iv_rank, trend_strength)
        
        # IV-adaptive strike selection
        if iv_rank < 30:
            # Very low IV → buy ATM
            target_delta = -0.50
        elif iv_rank < 40:
            # Low IV → slightly OTM
            target_delta = -0.40
        else:
            # Medium IV → more OTM
            target_delta = -0.30
        
        # Find strike by delta
        strike = self._find_strike_by_delta(option_chain, target_delta, 'put', dte)
        cost = self._get_option_cost(option_chain, strike, 'put', dte)
        
        # Position sizing
        max_loss_per_contract = cost * 100
        contracts = self.risk_manager.calculate_position_size(max_loss_per_contract)
        
        # Calculate metrics
        total_cost = cost * 100 * contracts
        
        return {
            'strategy': 'LONG_PUT',
            'action': 'BUY',
            'option_type': 'PUT',
            'strike': strike,
            'dte': dte,
            'contracts': contracts,
            'cost_per_contract': cost * 100,
            'total_cost': total_cost,
            'max_loss': total_cost,
            'max_profit': 'Unlimited',
            'breakeven': strike - cost,
            'target_delta': target_delta,
            'iv_rank': iv_rank,
            'trend_strength': trend_strength
        }
    
    def _generate_bull_call_spread(self, option_chain: pd.DataFrame, features: Dict,
                                   current_price: float) -> Dict:
        """
        Generate parameters for BULL CALL SPREAD.
        
        Strategy: Buy ATM call, sell OTM call
        Best when: Medium IV + Moderate bullish trend
        """
        iv_rank = features.get('iv_rank', 50)
        trend_strength = self._classify_trend_strength(features)
        
        # Select DTE
        dte = self._select_optimal_dte(option_chain, 'BULL_CALL_SPREAD', iv_rank, trend_strength)
        
        # IV-adaptive strike selection
        if iv_rank < 50:
            # Lower IV → tighter spread (more leverage)
            long_delta = 0.50  # ATM
            short_delta = 0.30  # Moderate OTM
        else:
            # Higher IV → wider spread (more premium)
            long_delta = 0.60  # ITM
            short_delta = 0.25  # Further OTM
        
        # Find strikes
        long_strike = self._find_strike_by_delta(option_chain, long_delta, 'call', dte)
        short_strike = self._find_strike_by_delta(option_chain, short_delta, 'call', dte)
        
        # Get costs
        long_cost = self._get_option_cost(option_chain, long_strike, 'call', dte)
        short_credit = self._get_option_bid(option_chain, short_strike, 'call', dte)
        
        # Calculate spread metrics
        net_debit = (long_cost - short_credit) * 100
        spread_width = (short_strike - long_strike) * 100
        max_profit = spread_width - net_debit
        
        # Position sizing
        contracts = self.risk_manager.calculate_position_size(net_debit)
        
        # Calculate totals
        total_debit = net_debit * contracts
        total_max_profit = max_profit * contracts
        
        return {
            'strategy': 'BULL_CALL_SPREAD',
            'long_strike': long_strike,
            'short_strike': short_strike,
            'dte': dte,
            'contracts': contracts,
            'net_debit': net_debit,
            'total_debit': total_debit,
            'max_profit': max_profit,
            'total_max_profit': total_max_profit,
            'max_loss': net_debit,
            'total_max_loss': total_debit,
            'breakeven': long_strike + (net_debit / 100),
            'spread_width': spread_width / 100,
            'risk_reward_ratio': max_profit / net_debit if net_debit > 0 else 0,
            'iv_rank': iv_rank
        }
    
    def _generate_bear_put_spread(self, option_chain: pd.DataFrame, features: Dict,
                                  current_price: float) -> Dict:
        """
        Generate parameters for BEAR PUT SPREAD.
        
        Strategy: Buy ATM put, sell OTM put
        Best when: Medium IV + Moderate bearish trend
        """
        iv_rank = features.get('iv_rank', 50)
        trend_strength = self._classify_trend_strength(features)
        
        # Select DTE
        dte = self._select_optimal_dte(option_chain, 'BEAR_PUT_SPREAD', iv_rank, trend_strength)
        
        # IV-adaptive strike selection
        if iv_rank < 50:
            # Lower IV → tighter spread
            long_delta = -0.50  # ATM
            short_delta = -0.30  # Moderate OTM
        else:
            # Higher IV → wider spread
            long_delta = -0.60  # ITM
            short_delta = -0.25  # Further OTM
        
        # Find strikes
        long_strike = self._find_strike_by_delta(option_chain, long_delta, 'put', dte)
        short_strike = self._find_strike_by_delta(option_chain, short_delta, 'put', dte)
        
        # Get costs
        long_cost = self._get_option_cost(option_chain, long_strike, 'put', dte)
        short_credit = self._get_option_bid(option_chain, short_strike, 'put', dte)
        
        # Calculate spread metrics
        net_debit = (long_cost - short_credit) * 100
        spread_width = (long_strike - short_strike) * 100
        max_profit = spread_width - net_debit
        
        # Position sizing
        contracts = self.risk_manager.calculate_position_size(net_debit)
        
        # Calculate totals
        total_debit = net_debit * contracts
        total_max_profit = max_profit * contracts
        
        return {
            'strategy': 'BEAR_PUT_SPREAD',
            'long_strike': long_strike,
            'short_strike': short_strike,
            'dte': dte,
            'contracts': contracts,
            'net_debit': net_debit,
            'total_debit': total_debit,
            'max_profit': max_profit,
            'total_max_profit': total_max_profit,
            'max_loss': net_debit,
            'total_max_loss': total_debit,
            'breakeven': long_strike - (net_debit / 100),
            'spread_width': spread_width / 100,
            'risk_reward_ratio': max_profit / net_debit if net_debit > 0 else 0,
            'iv_rank': iv_rank
        }
    
    def _generate_long_straddle(self, option_chain: pd.DataFrame, features: Dict,
                                current_price: float) -> Dict:
        """
        Generate parameters for LONG STRADDLE.
        
        Strategy: Buy ATM call + ATM put
        Best when: Low IV + Expecting big move
        """
        iv_rank = features.get('iv_rank', 50)
        
        # Select DTE (prefer longer for straddles)
        dte = self._select_optimal_dte(option_chain, 'LONG_STRADDLE', iv_rank, 'MODERATE')
        
        # Find ATM strike (50 delta for both)
        call_strike = self._find_strike_by_delta(option_chain, 0.50, 'call', dte)
        put_strike = self._find_strike_by_delta(option_chain, -0.50, 'put', dte)
        
        # Use same strike (ATM)
        atm_strike = (call_strike + put_strike) / 2
        atm_strike = self._find_strike_by_price(option_chain, atm_strike, 'call', dte)
        
        # Get costs
        call_cost = self._get_option_cost(option_chain, atm_strike, 'call', dte)
        put_cost = self._get_option_cost(option_chain, atm_strike, 'put', dte)
        
        # Calculate metrics
        total_cost_per_contract = (call_cost + put_cost) * 100
        
        # Position sizing
        contracts = self.risk_manager.calculate_position_size(total_cost_per_contract)
        
        # Calculate totals
        total_cost = total_cost_per_contract * contracts
        breakeven_up = atm_strike + (call_cost + put_cost)
        breakeven_down = atm_strike - (call_cost + put_cost)
        
        return {
            'strategy': 'LONG_STRADDLE',
            'strike': atm_strike,
            'dte': dte,
            'contracts': contracts,
            'call_cost': call_cost * 100,
            'put_cost': put_cost * 100,
            'cost_per_contract': total_cost_per_contract,
            'total_cost': total_cost,
            'max_loss': total_cost,
            'max_profit': 'Unlimited',
            'breakeven_up': breakeven_up,
            'breakeven_down': breakeven_down,
            'breakeven_range': breakeven_up - breakeven_down,
            'iv_rank': iv_rank
        }
    
    def _generate_long_strangle(self, option_chain: pd.DataFrame, features: Dict,
                                current_price: float) -> Dict:
        """
        Generate parameters for LONG STRANGLE.
        
        Strategy: Buy OTM call + OTM put
        Best when: Low IV + Expecting big move (cheaper than straddle)
        """
        iv_rank = features.get('iv_rank', 50)
        
        # Select DTE
        dte = self._select_optimal_dte(option_chain, 'LONG_STRANGLE', iv_rank, 'MODERATE')
        
        # IV-adaptive strike selection
        if iv_rank < 30:
            # Very low IV → closer to ATM (more leverage)
            call_delta = 0.35
            put_delta = -0.35
        else:
            # Higher IV → further OTM (cheaper)
            call_delta = 0.25
            put_delta = -0.25
        
        # Find strikes
        call_strike = self._find_strike_by_delta(option_chain, call_delta, 'call', dte)
        put_strike = self._find_strike_by_delta(option_chain, put_delta, 'put', dte)
        
        # Get costs
        call_cost = self._get_option_cost(option_chain, call_strike, 'call', dte)
        put_cost = self._get_option_cost(option_chain, put_strike, 'put', dte)
        
        # Calculate metrics
        total_cost_per_contract = (call_cost + put_cost) * 100
        
        # Position sizing
        contracts = self.risk_manager.calculate_position_size(total_cost_per_contract)
        
        # Calculate totals
        total_cost = total_cost_per_contract * contracts
        breakeven_up = call_strike + (call_cost + put_cost)
        breakeven_down = put_strike - (call_cost + put_cost)
        
        return {
            'strategy': 'LONG_STRANGLE',
            'call_strike': call_strike,
            'put_strike': put_strike,
            'dte': dte,
            'contracts': contracts,
            'call_cost': call_cost * 100,
            'put_cost': put_cost * 100,
            'cost_per_contract': total_cost_per_contract,
            'total_cost': total_cost,
            'max_loss': total_cost,
            'max_profit': 'Unlimited',
            'breakeven_up': breakeven_up,
            'breakeven_down': breakeven_down,
            'breakeven_range': breakeven_up - breakeven_down,
            'strike_width': call_strike - put_strike,
            'iv_rank': iv_rank
        }
    
    def _generate_iron_condor(self, option_chain: pd.DataFrame, features: Dict,
                              current_price: float) -> Dict:
        """
        Generate parameters for IRON CONDOR.
        
        Strategy: Sell OTM put spread + OTM call spread
        Best when: High IV + Ranging market
        """
        iv_rank = features.get('iv_rank', 50)
        
        # Select DTE (shorter for high IV)
        dte = self._select_optimal_dte(option_chain, 'IRON_CONDOR', iv_rank, 'WEAK')
        
        # IV-adaptive strike selection
        if iv_rank > 70:
            # Very high IV → wider wings (more premium, more room)
            put_short_delta = -0.20
            put_long_delta = -0.10
            call_short_delta = 0.20
            call_long_delta = 0.10
        else:
            # High IV → standard wings
            put_short_delta = -0.25
            put_long_delta = -0.15
            call_short_delta = 0.25
            call_long_delta = 0.15
        
        # Find strikes
        put_short_strike = self._find_strike_by_delta(option_chain, put_short_delta, 'put', dte)
        put_long_strike = self._find_strike_by_delta(option_chain, put_long_delta, 'put', dte)
        call_short_strike = self._find_strike_by_delta(option_chain, call_short_delta, 'call', dte)
        call_long_strike = self._find_strike_by_delta(option_chain, call_long_delta, 'call', dte)
        
        # Get prices
        put_short_credit = self._get_option_bid(option_chain, put_short_strike, 'put', dte)
        put_long_cost = self._get_option_cost(option_chain, put_long_strike, 'put', dte)
        call_short_credit = self._get_option_bid(option_chain, call_short_strike, 'call', dte)
        call_long_cost = self._get_option_cost(option_chain, call_long_strike, 'call', dte)
        
        # Calculate metrics
        net_credit = (put_short_credit + call_short_credit - put_long_cost - call_long_cost) * 100
        put_spread_width = (put_short_strike - put_long_strike) * 100
        call_spread_width = (call_long_strike - call_short_strike) * 100
        max_loss = max(put_spread_width, call_spread_width) - net_credit
        
        # Position sizing
        contracts = self.risk_manager.calculate_position_size(max_loss)
        
        # Calculate totals
        total_credit = net_credit * contracts
        total_max_loss = max_loss * contracts
        
        return {
            'strategy': 'IRON_CONDOR',
            'put_short_strike': put_short_strike,
            'put_long_strike': put_long_strike,
            'call_short_strike': call_short_strike,
            'call_long_strike': call_long_strike,
            'dte': dte,
            'contracts': contracts,
            'net_credit': net_credit,
            'total_credit': total_credit,
            'max_profit': net_credit,
            'total_max_profit': total_credit,
            'max_loss': max_loss,
            'total_max_loss': total_max_loss,
            'breakeven_down': put_short_strike - (net_credit / 100),
            'breakeven_up': call_short_strike + (net_credit / 100),
            'profit_zone_width': call_short_strike - put_short_strike,
            'risk_reward_ratio': net_credit / max_loss if max_loss > 0 else 0,
            'iv_rank': iv_rank
        }
    
    def _generate_iron_butterfly(self, option_chain: pd.DataFrame, features: Dict,
                                 current_price: float) -> Dict:
        """
        Generate parameters for IRON BUTTERFLY.
        
        Strategy: Sell ATM straddle + buy OTM strangle
        Best when: Very high IV + Very ranging market
        """
        iv_rank = features.get('iv_rank', 50)
        
        # Select DTE (shorter for very high IV)
        dte = self._select_optimal_dte(option_chain, 'IRON_BUTTERFLY', iv_rank, 'WEAK')
        
        # Find ATM strike
        atm_strike = self._find_strike_by_delta(option_chain, 0.50, 'call', dte)
        
        # IV-adaptive wing width
        if iv_rank > 75:
            # Very high IV → wider wings
            wing_pct = 0.07  # 7% wings
        else:
            # High IV → standard wings
            wing_pct = 0.05  # 5% wings
        
        # Find wing strikes
        long_put_strike = self._find_strike_by_price(
            option_chain, atm_strike * (1 - wing_pct), 'put', dte
        )
        long_call_strike = self._find_strike_by_price(
            option_chain, atm_strike * (1 + wing_pct), 'call', dte
        )
        
        # Get prices
        atm_put_credit = self._get_option_bid(option_chain, atm_strike, 'put', dte)
        atm_call_credit = self._get_option_bid(option_chain, atm_strike, 'call', dte)
        long_put_cost = self._get_option_cost(option_chain, long_put_strike, 'put', dte)
        long_call_cost = self._get_option_cost(option_chain, long_call_strike, 'call', dte)
        
        # Calculate metrics
        net_credit = (atm_put_credit + atm_call_credit - long_put_cost - long_call_cost) * 100
        wing_width = max(
            (atm_strike - long_put_strike) * 100,
            (long_call_strike - atm_strike) * 100
        )
        max_loss = wing_width - net_credit
        
        # Position sizing
        contracts = self.risk_manager.calculate_position_size(max_loss)
        
        # Calculate totals
        total_credit = net_credit * contracts
        total_max_loss = max_loss * contracts
        
        return {
            'strategy': 'IRON_BUTTERFLY',
            'center_strike': atm_strike,
            'long_put_strike': long_put_strike,
            'long_call_strike': long_call_strike,
            'dte': dte,
            'contracts': contracts,
            'net_credit': net_credit,
            'total_credit': total_credit,
            'max_profit': net_credit,
            'total_max_profit': total_credit,
            'max_loss': max_loss,
            'total_max_loss': total_max_loss,
            'breakeven_down': atm_strike - (net_credit / 100),
            'breakeven_up': atm_strike + (net_credit / 100),
            'profit_zone_width': (net_credit / 100) * 2,
            'wing_width': wing_width / 100,
            'risk_reward_ratio': net_credit / max_loss if max_loss > 0 else 0,
            'iv_rank': iv_rank
        }
    
    def _generate_calendar_spread(self, option_chain: pd.DataFrame, features: Dict,
                                  current_price: float) -> Dict:
        """
        Generate parameters for CALENDAR SPREAD.
        
        Strategy: Sell near-term option, buy far-term option (same strike)
        Best when: Low IV + Neutral outlook
        """
        iv_rank = features.get('iv_rank', 50)
        
        # Find available DTEs
        available_dtes = sorted(option_chain['dte'].unique())
        
        # Select near and far DTE
        near_dte = min(available_dtes, key=lambda x: abs(x - 21))  # ~3 weeks
        far_dte = min([d for d in available_dtes if d > near_dte + 14], 
                     key=lambda x: abs(x - 45), default=near_dte + 30)  # ~6 weeks
        
        # Find ATM strike
        atm_strike = self._find_strike_by_delta(option_chain, 0.50, 'call', near_dte)
        
        # Determine call or put based on slight bias
        rsi = features.get('rsi_14', 50)
        option_type = 'call' if rsi > 50 else 'put'
        
        # Get prices
        near_credit = self._get_option_bid(option_chain, atm_strike, option_type, near_dte)
        far_cost = self._get_option_cost(option_chain, atm_strike, option_type, far_dte)
        
        # Calculate metrics
        net_debit = (far_cost - near_credit) * 100
        
        # Position sizing
        contracts = self.risk_manager.calculate_position_size(net_debit)
        
        # Calculate totals
        total_debit = net_debit * contracts
        
        return {
            'strategy': 'CALENDAR_SPREAD',
            'strike': atm_strike,
            'option_type': option_type.upper(),
            'near_dte': near_dte,
            'far_dte': far_dte,
            'contracts': contracts,
            'net_debit': net_debit,
            'total_debit': total_debit,
            'max_loss': net_debit,
            'total_max_loss': total_debit,
            'max_profit': 'Variable (depends on IV expansion)',
            'note': 'Profit maximized if price stays near strike at near expiration',
            'iv_rank': iv_rank
        }
    
    def _generate_diagonal_spread(self, option_chain: pd.DataFrame, features: Dict,
                                  current_price: float) -> Dict:
        """
        Generate parameters for DIAGONAL SPREAD.
        
        Strategy: Sell near-term OTM option, buy far-term ATM option
        Best when: Medium IV + Slight directional bias
        """
        iv_rank = features.get('iv_rank', 50)
        rsi = features.get('rsi_14', 50)
        
        # Find available DTEs
        available_dtes = sorted(option_chain['dte'].unique())
        
        # Select near and far DTE
        near_dte = min(available_dtes, key=lambda x: abs(x - 21))
        far_dte = min([d for d in available_dtes if d > near_dte + 14],
                     key=lambda x: abs(x - 45), default=near_dte + 30)
        
        # Determine direction based on bias
        if rsi > 55:
            # Bullish bias → diagonal call spread
            option_type = 'call'
            long_delta = 0.50  # ATM
            short_delta = 0.30  # OTM
        else:
            # Bearish bias → diagonal put spread
            option_type = 'put'
            long_delta = -0.50  # ATM
            short_delta = -0.30  # OTM
        
        # Find strikes
        long_strike = self._find_strike_by_delta(option_chain, long_delta, option_type, far_dte)
        short_strike = self._find_strike_by_delta(option_chain, short_delta, option_type, near_dte)
        
        # Get prices
        long_cost = self._get_option_cost(option_chain, long_strike, option_type, far_dte)
        short_credit = self._get_option_bid(option_chain, short_strike, option_type, near_dte)
        
        # Calculate metrics
        net_debit = (long_cost - short_credit) * 100
        
        # Position sizing
        contracts = self.risk_manager.calculate_position_size(net_debit)
        
        # Calculate totals
        total_debit = net_debit * contracts
        
        return {
            'strategy': 'DIAGONAL_SPREAD',
            'option_type': option_type.upper(),
            'long_strike': long_strike,
            'short_strike': short_strike,
            'near_dte': near_dte,
            'far_dte': far_dte,
            'contracts': contracts,
            'net_debit': net_debit,
            'total_debit': total_debit,
            'max_loss': net_debit,
            'total_max_loss': total_debit,
            'max_profit': 'Variable (depends on price movement and IV)',
            'bias': 'Bullish' if option_type == 'call' else 'Bearish',
            'note': 'Roll short option at expiration to continue position',
            'iv_rank': iv_rank
        }


# Example usage
if __name__ == "__main__":
    print("Enhanced Parameter Generator with Risk Management")
    print("=" * 60)
    print("\nFeatures:")
    print("  ✓ IV-adaptive strike selection")
    print("  ✓ Delta-based targeting")
    print("  ✓ Trend-strength adjustments")
    print("  ✓ Position sizing (max 2% risk)")
    print("  ✓ Risk/reward validation")
    print("\nSupported Strategies: 10")
    print("  - Long Call/Put")
    print("  - Bull Call Spread / Bear Put Spread")
    print("  - Long Straddle / Long Strangle")
    print("  - Iron Condor / Iron Butterfly")
    print("  - Calendar Spread / Diagonal Spread")
