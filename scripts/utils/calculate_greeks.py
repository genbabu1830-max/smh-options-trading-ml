#!/usr/bin/env python3
"""
Calculate Greeks (Delta, Gamma, Theta, Vega) from OHLCV data
Using Black-Scholes model
"""

import numpy as np
import pandas as pd
from datetime import datetime

# Pure numpy implementation of normal distribution (no scipy needed)
def norm_cdf(x):
    """Cumulative distribution function for standard normal distribution"""
    return 0.5 * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

def norm_pdf(x):
    """Probability density function for standard normal distribution"""
    return np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)

def black_scholes_call(S, K, T, r, sigma):
    """
    Calculate Black-Scholes call option price
    
    S: Current stock price
    K: Strike price
    T: Time to expiration (in years)
    r: Risk-free rate
    sigma: Volatility (implied volatility)
    """
    if T <= 0:
        return max(S - K, 0)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    call_price = S * norm_cdf(d1) - K * np.exp(-r * T) * norm_cdf(d2)
    return call_price

def black_scholes_put(S, K, T, r, sigma):
    """
    Calculate Black-Scholes put option price
    """
    if T <= 0:
        return max(K - S, 0)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    put_price = K * np.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
    return put_price

def calculate_implied_volatility(option_price, S, K, T, r, option_type='call'):
    """
    Calculate implied volatility using Newton-Raphson method
    
    option_price: Market price of the option
    S: Current stock price
    K: Strike price
    T: Time to expiration (in years)
    r: Risk-free rate
    option_type: 'call' or 'put'
    """
    if T <= 0:
        return 0
    
    # Define the objective function
    def objective(sigma):
        if option_type == 'call':
            return black_scholes_call(S, K, T, r, sigma) - option_price
        else:
            return black_scholes_put(S, K, T, r, sigma) - option_price
    
    try:
        # Use Newton-Raphson method to find IV
        sigma = 0.3  # Initial guess
        for i in range(100):
            price_diff = objective(sigma)
            if abs(price_diff) < 0.001:  # Converged
                return sigma
            
            # Calculate vega for Newton-Raphson
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            vega = S * norm_pdf(d1) * np.sqrt(T)
            
            if vega < 0.0001:  # Avoid division by zero
                return None
            
            # Newton-Raphson update
            sigma = sigma - price_diff / vega
            
            if sigma <= 0 or sigma > 5:  # Out of bounds
                return None
        
        return sigma if sigma > 0 else None
    except:
        return None

def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option Greeks
    
    Returns: dict with delta, gamma, theta, vega, rho
    """
    if T <= 0:
        # For expired options
        if option_type == 'call':
            delta = 1.0 if S > K else 0.0
        else:
            delta = -1.0 if S < K else 0.0
        return {
            'delta': delta,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # Delta
    if option_type == 'call':
        delta = norm_cdf(d1)
    else:
        delta = -norm_cdf(-d1)
    
    # Gamma (same for call and put)
    gamma = norm_pdf(d1) / (S * sigma * np.sqrt(T))
    
    # Vega (same for call and put) - per 1% change in volatility
    vega = S * norm_pdf(d1) * np.sqrt(T) / 100
    
    # Theta (per day)
    if option_type == 'call':
        theta = (-(S * norm_pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * norm_cdf(d2)) / 365
    else:
        theta = (-(S * norm_pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * norm_cdf(-d2)) / 365
    
    # Rho (per 1% change in interest rate)
    if option_type == 'call':
        rho = K * T * np.exp(-r * T) * norm_cdf(d2) / 100
    else:
        rho = -K * T * np.exp(-r * T) * norm_cdf(-d2) / 100
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }

def calculate_days_to_expiration(expiration_date, current_date):
    """
    Calculate days to expiration
    """
    if isinstance(expiration_date, str):
        exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
    else:
        exp_date = expiration_date
    
    if isinstance(current_date, str):
        curr_date = datetime.strptime(current_date, '%Y-%m-%d')
    else:
        curr_date = current_date
    
    days = (exp_date - curr_date).days
    return max(days, 0)

# Example usage
if __name__ == "__main__":
    print("="*70)
    print("GREEKS CALCULATION FROM OHLCV DATA")
    print("="*70)
    print()
    
    # Example: IWM Nov 29, 2024 $245 Call
    # Data from our S3 download
    underlying_price = 241.87  # IWM price on Nov 29, 2024
    strike_price = 245.0
    option_price = 0.09  # Close price from OHLCV
    expiration_date = '2024-11-29'
    current_date = '2024-11-29'
    option_type = 'call'
    risk_free_rate = 0.045  # 4.5% (approximate treasury rate)
    
    # Calculate time to expiration
    days_to_exp = calculate_days_to_expiration(expiration_date, current_date)
    time_to_exp = days_to_exp / 365.0
    
    print(f"Contract: IWM {expiration_date} ${strike_price} {option_type.upper()}")
    print(f"Underlying Price: ${underlying_price}")
    print(f"Option Price: ${option_price}")
    print(f"Days to Expiration: {days_to_exp}")
    print(f"Risk-free Rate: {risk_free_rate:.2%}")
    print()
    
    # Step 1: Calculate Implied Volatility
    print("Step 1: Calculating Implied Volatility...")
    iv = calculate_implied_volatility(
        option_price, 
        underlying_price, 
        strike_price, 
        time_to_exp, 
        risk_free_rate, 
        option_type
    )
    
    if iv is not None:
        print(f"✓ Implied Volatility: {iv:.2%}")
        print()
        
        # Step 2: Calculate Greeks
        print("Step 2: Calculating Greeks...")
        greeks = calculate_greeks(
            underlying_price,
            strike_price,
            time_to_exp,
            risk_free_rate,
            iv,
            option_type
        )
        
        print(f"✓ Delta: {greeks['delta']:.6f}")
        print(f"✓ Gamma: {greeks['gamma']:.6f}")
        print(f"✓ Theta: {greeks['theta']:.6f} (per day)")
        print(f"✓ Vega: {greeks['vega']:.6f} (per 1% IV change)")
        print(f"✓ Rho: {greeks['rho']:.6f} (per 1% rate change)")
    else:
        print("✗ Could not calculate IV (option may be too far OTM/ITM)")
    
    print()
    print("="*70)
    print()
    
    # Example 2: ITM option
    print("Example 2: ITM Option")
    print("-"*70)
    underlying_price = 241.87
    strike_price = 230.0
    option_price = 12.50  # Approximate ITM value
    
    print(f"Contract: IWM {expiration_date} ${strike_price} {option_type.upper()}")
    print(f"Underlying: ${underlying_price}, Strike: ${strike_price}, Price: ${option_price}")
    print()
    
    iv = calculate_implied_volatility(
        option_price, 
        underlying_price, 
        strike_price, 
        time_to_exp, 
        risk_free_rate, 
        option_type
    )
    
    if iv:
        greeks = calculate_greeks(
            underlying_price, strike_price, time_to_exp, 
            risk_free_rate, iv, option_type
        )
        print(f"IV: {iv:.2%}")
        print(f"Delta: {greeks['delta']:.4f}, Gamma: {greeks['gamma']:.6f}")
        print(f"Theta: {greeks['theta']:.4f}, Vega: {greeks['vega']:.4f}")


def black_scholes_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Calculate Black-Scholes Greeks
    Wrapper function that returns dict with all Greeks
    """
    return calculate_greeks(S, K, T, r, sigma, option_type)

def calculate_0dte_greeks(S, K, option_type, option_price):
    """
    Calculate Greeks for 0DTE and 1DTE options using intrinsic value method
    
    For very short-dated options, IV calculation is unstable.
    Instead, we use the option price directly to estimate Greeks.
    
    Parameters:
    - S: Stock price
    - K: Strike price
    - option_type: 'call' or 'put'
    - option_price: Market price of the option
    
    Returns: dict with delta, gamma, theta, vega, implied_volatility
    """
    # Calculate intrinsic value
    if option_type == 'call':
        intrinsic = max(S - K, 0)
    else:
        intrinsic = max(K - S, 0)
    
    # Time value
    time_value = max(option_price - intrinsic, 0)
    
    # Moneyness
    moneyness = S / K if K > 0 else 1.0
    
    # Delta estimation based on moneyness
    if option_type == 'call':
        if moneyness > 1.02:  # ITM
            delta = 1.0
        elif moneyness < 0.98:  # OTM
            delta = 0.0
        else:  # ATM
            # Linear interpolation for ATM
            delta = (moneyness - 0.98) / 0.04
    else:  # put
        if moneyness > 1.02:  # OTM
            delta = 0.0
        elif moneyness < 0.98:  # ITM
            delta = -1.0
        else:  # ATM
            delta = -1.0 + (moneyness - 0.98) / 0.04
    
    # Gamma is highest ATM, zero for deep ITM/OTM
    if 0.98 <= moneyness <= 1.02:
        gamma = 0.1  # High gamma for ATM 0DTE
    else:
        gamma = 0.0
    
    # Theta is very high for 0DTE (time decay accelerates)
    # Estimate based on time value
    theta = -time_value  # All time value decays in 1 day
    
    # Vega is low for 0DTE (little sensitivity to IV changes)
    vega = time_value * 0.1
    
    # Estimate IV from time value
    # For 0DTE, use a simple approximation
    if time_value > 0.01 and 0.98 <= moneyness <= 1.02:
        # ATM options: IV roughly proportional to time value
        implied_volatility = time_value / S * 100  # Rough approximation
        implied_volatility = max(0.1, min(implied_volatility, 2.0))  # Clamp between 10% and 200%
    else:
        implied_volatility = 0.25  # Default 25% for ITM/OTM
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'implied_volatility': implied_volatility,
        'rho': 0.0  # Negligible for 0DTE
    }

def get_historical_greeks_iv(options_df, stock_price, date):
    """
    Smart handling of all DTE ranges
    
    Parameters:
    - options_df: DataFrame with columns ['ticker', 'strike', 'type', 'expiration', 'close']
    - stock_price: Current underlying stock price
    - date: Current date (for calculating DTE)
    
    Returns:
    - DataFrame with calculated Greeks and IV for each option
    """
    results = []
    
    for idx, row in options_df.iterrows():
        expiration = pd.to_datetime(row['expiration'])
        
        if isinstance(date, str):
            current_date = pd.to_datetime(date)
        else:
            current_date = pd.to_datetime(date)
        
        dte = (expiration - current_date).days
        
        if dte < 0:
            continue  # Expired
        elif dte == 0:
            # Use intrinsic value method
            greeks_iv = calculate_0dte_greeks(
                S=stock_price,
                K=row['strike'],
                option_type=row['type'],
                option_price=row['close']
            )
        elif dte == 1:
            # 1DTE is also unstable, use simplified method
            greeks_iv = calculate_0dte_greeks(
                S=stock_price,
                K=row['strike'],
                option_type=row['type'],
                option_price=row['close']
            )
        else:
            # 2+ DTE: Use Black-Scholes (works well)
            T = dte / 365
            iv = calculate_implied_volatility(
                option_price=row['close'],
                S=stock_price,
                K=row['strike'],
                T=T,
                r=0.04,
                option_type=row['type']
            )
            
            if iv is not None:
                greeks_iv = black_scholes_greeks(
                    S=stock_price,
                    K=row['strike'],
                    T=T,
                    r=0.04,
                    sigma=iv,
                    option_type=row['type']
                )
                greeks_iv['implied_volatility'] = iv
            else:
                continue
        
        results.append({
            'ticker': row['ticker'],
            'strike': row['strike'],
            'type': row['type'],
            'dte': dte,
            **greeks_iv
        })
    
    return pd.DataFrame(results)
