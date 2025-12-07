#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recommendation Agent - Strands Implementation
Generates daily options trade recommendations using ML + Rules
"""

import os
import sys
import json
import boto3
import joblib
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Strands
try:
    from strands_agents import Agent
    from strands_agents.tools import tool
    from strands_agents.models import BedrockModel
except ImportError:
    print("⚠️  Strands not installed. Install with: pip install strands-agents")
    # Fallback for development
    def tool(func):
        return func
    Agent = None
    BedrockModel = None

# Import our existing modules
from scripts.utils.feature_extractor import FeatureExtractor
from scripts.utils.parameter_generator import ParameterGenerator, RiskManager
from scripts.utils.model_loader import ModelLoader


class RecommendationAgent:
    """
    Recommendation Agent using Strands Framework
    
    Generates daily options trade recommendations using:
    - Stage 1: ML model predicts strategy (84.21% accuracy)
    - Stage 2: Rules generate parameters (80-90% accuracy)
    """
    
    def __init__(self, ticker: str = "SMH", use_s3: bool = False):
        """
        Initialize Recommendation Agent
        
        Args:
            ticker: Stock ticker (default: SMH)
            use_s3: Load models from S3 (default: False, uses local)
        """
        self.ticker = ticker
        self.use_s3 = use_s3
        
        # Initialize components
        print("🔧 Initializing Recommendation Agent...")
        
        # Load ML model
        source = 's3' if use_s3 else 'local'
        self.model_loader = ModelLoader(source=source)
        models = self.model_loader.load_models_for_ticker(ticker)
        self.ml_model = models['ml_model']
        self.label_encoder = models['label_encoder']
        self.feature_names = models['feature_names']
        print(f"✅ ML Model loaded ({len(self.feature_names)} features)")
        
        # Initialize feature extractor
        self.feature_extractor = FeatureExtractor()
        print("✅ Feature Extractor initialized")
        
        # Initialize parameter generator with risk manager
        self.risk_manager = RiskManager(
            account_size=10000,
            risk_per_trade=0.02
        )
        self.parameter_generator = ParameterGenerator(risk_manager=self.risk_manager)
        print("✅ Parameter Generator initialized")
        
        # Initialize Strands agent (if available)
        if Agent and BedrockModel:
            self._init_strands_agent()
        else:
            print("⚠️  Running without Strands (development mode)")
            self.agent = None
    
    def _init_strands_agent(self):
        """Initialize Strands agent with tools"""
        
        # System prompt for the agent
        system_prompt = """You are an expert options trading recommendation agent.

Your role is to generate daily options trade recommendations using a proven 2-stage system:

STAGE 1 (ML): Predict optimal strategy
- Use trained ML model (84.21% accuracy)
- Input: 84 aggregated market features
- Output: Strategy name + confidence

STAGE 2 (Rules): Generate trade parameters
- Use professional rules-based logic (80-90% accuracy)
- Input: Strategy + market data + features
- Output: Specific strikes, DTE, sizing, etc.

IMPORTANT:
- Always use BOTH stages in sequence
- Never skip feature extraction
- Stage 1 predicts WHAT strategy
- Stage 2 determines HOW to execute
- Validate risk before recommending

Your recommendations are used for real trading, so accuracy is critical.

Available tools:
1. fetch_market_data() - Get option chain and price history
2. extract_features() - Convert to 84 features
3. predict_strategy() - ML prediction (Stage 1)
4. generate_parameters() - Rules-based params (Stage 2)
5. format_recommendation() - Format final output
"""
        
        # Initialize Bedrock model (Claude Haiku for cost efficiency)
        model = BedrockModel(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            temperature=0.1,  # Low temperature for consistency
            region_name="us-east-1"
        )
        
        # Create agent with tools
        self.agent = Agent(
            model=model,
            tools=[
                self.fetch_market_data,
                self.extract_features,
                self.predict_strategy,
                self.generate_parameters,
                self.format_recommendation
            ],
            system_prompt=system_prompt,
            name="RecommendationAgent"
        )
        
        print("✅ Strands Agent initialized")
    
    @tool
    def fetch_market_data(self, ticker: str = None, date: str = None) -> Dict[str, Any]:
        """
        Fetch current option chain and price history from Massive.com API.
        
        Args:
            ticker: Stock ticker symbol (default: self.ticker)
            date: Date for data (default: today)
        
        Returns:
            Dictionary with option_chain, price_history, and current_price
        """
        if ticker is None:
            ticker = self.ticker
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📊 Fetching market data for {ticker} on {date}...")
        
        # TODO: Implement Massive.com API call
        # For now, return mock data structure
        return {
            'ticker': ticker,
            'date': date,
            'option_chain': {},  # Will be DataFrame
            'price_history': {},  # Will be DataFrame
            'current_price': 236.80,
            'status': 'mock_data'
        }
    
    @tool
    def extract_features(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract 84 features from raw market data using FeatureExtractor.
        
        Args:
            market_data: Dictionary with option_chain and price_history
        
        Returns:
            Dictionary with 84 features ready for ML model
        """
        print("🔬 Extracting features...")
        
        # Convert market data to DataFrames
        option_chain = pd.DataFrame(market_data.get('option_chain', {}))
        price_history = pd.DataFrame(market_data.get('price_history', {}))
        current_date = market_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Extract features using our existing code
        features = self.feature_extractor.extract_features(
            option_chain=option_chain,
            price_history=price_history,
            current_date=current_date
        )
        
        print(f"✅ Extracted {len(features)} features")
        
        return features
    
    @tool
    def predict_strategy(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use ML model to predict optimal options strategy (Stage 1).
        
        Args:
            features: Dictionary with 84 features
        
        Returns:
            Dictionary with strategy name, confidence, and alternatives
        """
        print("🤖 Predicting strategy (Stage 1 - ML)...")
        
        # Convert features to DataFrame with correct column order
        feature_df = pd.DataFrame([features])[self.feature_names]
        
        # Predict using ML model
        prediction = self.ml_model.predict(feature_df)[0]
        probabilities = self.ml_model.predict_proba(feature_df)[0]
        
        # Decode strategy name
        strategy = self.label_encoder.inverse_transform([prediction])[0]
        confidence = float(probabilities[prediction])
        
        # Get top 3 alternatives
        top_3_idx = probabilities.argsort()[-3:][::-1]
        alternatives = [
            {
                'strategy': self.label_encoder.inverse_transform([idx])[0],
                'confidence': float(probabilities[idx])
            }
            for idx in top_3_idx
        ]
        
        result = {
            'strategy': strategy,
            'confidence': confidence,
            'alternatives': alternatives,
            'model_version': 'v1.0',
            'model_accuracy': 0.8421
        }
        
        print(f"✅ Predicted: {strategy} (confidence: {confidence:.1%})")
        
        return result
    
    @tool
    def generate_parameters(self, strategy: str, market_data: Dict[str, Any], 
                          features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trade parameters using rules-based logic (Stage 2).
        
        Args:
            strategy: Strategy name from ML prediction
            market_data: Raw market data with option chain
            features: Extracted features
        
        Returns:
            Complete trade specification with strikes, DTE, sizing, etc.
        """
        print(f"📐 Generating parameters (Stage 2 - Rules) for {strategy}...")
        
        # Convert option chain back to DataFrame
        option_chain = pd.DataFrame(market_data.get('option_chain', {}))
        current_price = market_data.get('current_price', features.get('current_price', 236.80))
        
        # Generate parameters using our existing code
        parameters = self.parameter_generator.generate(
            strategy=strategy,
            option_chain=option_chain,
            features=features,
            current_price=current_price
        )
        
        # Add risk validation
        if 'max_loss' in parameters and 'max_profit' in parameters:
            max_loss = parameters.get('total_max_loss', parameters.get('max_loss', 0))
            max_profit = parameters.get('total_max_profit', parameters.get('max_profit', 0))
            
            # Handle unlimited profit strategies
            if isinstance(max_profit, str) and 'unlimited' in max_profit.lower():
                max_profit = abs(max_loss) * 3  # Estimate 3:1 reward
            
            validation = self.risk_manager.validate_trade(abs(max_loss), max_profit)
            parameters['risk_validation'] = validation
        
        print(f"✅ Parameters generated")
        
        return parameters
    
    @tool
    def format_recommendation(self, strategy: Dict[str, Any], 
                            parameters: Dict[str, Any], 
                            features: Dict[str, Any],
                            market_data: Dict[str, Any]) -> str:
        """
        Format the complete recommendation for user presentation.
        
        Args:
            strategy: Strategy prediction with confidence
            parameters: Trade parameters
            features: Market features
            market_data: Raw market data
        
        Returns:
            Formatted recommendation text
        """
        print("📝 Formatting recommendation...")
        
        strategy_name = strategy['strategy']
        confidence = strategy['confidence']
        
        output = f"""
{'=' * 70}
📊 OPTIONS TRADE RECOMMENDATION
{'=' * 70}

🎯 STRATEGY: {strategy_name}
   Confidence: {confidence:.1%}
   Model Accuracy: {strategy['model_accuracy']:.1%}
   Date: {market_data.get('date', datetime.now().strftime('%Y-%m-%d'))}
   Ticker: {market_data.get('ticker', self.ticker)}

💰 TRADE PARAMETERS:
"""
        
        # Add strategy-specific details
        if strategy_name == 'IRON_CONDOR':
            output += f"""
   Put Spread: ${parameters.get('put_long_strike', 0):.0f} / ${parameters.get('put_short_strike', 0):.0f}
   Call Spread: ${parameters.get('call_short_strike', 0):.0f} / ${parameters.get('call_long_strike', 0):.0f}
   DTE: {parameters.get('dte', 0)} days
   Contracts: {parameters.get('contracts', 0)}
   
   Net Credit: ${parameters.get('total_credit', 0):.2f}
   Max Profit: ${parameters.get('total_max_profit', 0):.2f}
   Max Loss: ${parameters.get('total_max_loss', 0):.2f}
   
   Profit Zone: ${parameters.get('breakeven_down', 0):.2f} - ${parameters.get('breakeven_up', 0):.2f}
   Risk/Reward: {parameters.get('risk_reward_ratio', 0):.2f}
"""
        
        elif strategy_name in ['LONG_CALL', 'LONG_PUT']:
            output += f"""
   Strike: ${parameters.get('strike', 0):.0f}
   DTE: {parameters.get('dte', 0)} days
   Contracts: {parameters.get('contracts', 0)}
   
   Cost: ${parameters.get('total_cost', 0):.2f}
   Max Loss: ${parameters.get('max_loss', 0):.2f}
   Breakeven: ${parameters.get('breakeven', 0):.2f}
"""
        
        elif strategy_name in ['BULL_CALL_SPREAD', 'BEAR_PUT_SPREAD']:
            output += f"""
   Long Strike: ${parameters.get('long_strike', 0):.0f}
   Short Strike: ${parameters.get('short_strike', 0):.0f}
   DTE: {parameters.get('dte', 0)} days
   Contracts: {parameters.get('contracts', 0)}
   
   Net Debit: ${parameters.get('total_debit', 0):.2f}
   Max Profit: ${parameters.get('total_max_profit', 0):.2f}
   Max Loss: ${parameters.get('total_max_loss', 0):.2f}
   Breakeven: ${parameters.get('breakeven', 0):.2f}
"""
        
        # Add market conditions
        current_price = market_data.get('current_price', features.get('current_price', 0))
        iv_rank = features.get('iv_rank', 0)
        trend_regime = features.get('trend_regime', 2)
        trend_names = ['Strong Down', 'Weak Down', 'Ranging', 'Weak Up', 'Strong Up']
        
        output += f"""
📈 MARKET CONDITIONS:
   Current Price: ${current_price:.2f}
   IV Rank: {iv_rank:.1f}%
   Trend: {trend_names[trend_regime] if 0 <= trend_regime < 5 else 'Unknown'}
   ADX: {features.get('adx_14', 0):.1f}
   RSI: {features.get('rsi_14', 0):.1f}
"""
        
        # Add risk validation
        if 'risk_validation' in parameters:
            validation = parameters['risk_validation']
            status_emoji = '✅' if validation.get('approved', False) else '❌'
            
            output += f"""
✅ RISK VALIDATION:
   Status: {'APPROVED ' + status_emoji if validation.get('approved', False) else 'REJECTED ' + status_emoji}
   Risk/Reward: {validation.get('risk_reward_ratio', 0):.2f}
   Risk %: {validation.get('risk_percentage', 0):.2%}
   Position Size: ${validation.get('position_size', 0):.2f}
"""
        
        # Add alternatives
        if strategy.get('alternatives'):
            output += f"\n🔄 ALTERNATIVE STRATEGIES:\n"
            for alt in strategy['alternatives'][1:3]:  # Top 2 alternatives
                output += f"   {alt['strategy']}: {alt['confidence']:.1%}\n"
        
        output += f"\n{'=' * 70}\n"
        
        return output
    
    def generate_recommendation(self, date: str = None) -> Dict[str, Any]:
        """
        Generate complete trade recommendation (main entry point).
        
        Args:
            date: Date for recommendation (default: today)
        
        Returns:
            Complete recommendation dictionary
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n🚀 Generating recommendation for {self.ticker} on {date}...")
        print("=" * 70)
        
        # Step 1: Fetch market data
        market_data = self.fetch_market_data(ticker=self.ticker, date=date)
        
        # Step 2: Extract features
        features = self.extract_features(market_data)
        
        # Step 3: Predict strategy (Stage 1 - ML)
        strategy = self.predict_strategy(features)
        
        # Step 4: Generate parameters (Stage 2 - Rules)
        parameters = self.generate_parameters(
            strategy=strategy['strategy'],
            market_data=market_data,
            features=features
        )
        
        # Step 5: Format recommendation
        formatted = self.format_recommendation(
            strategy=strategy,
            parameters=parameters,
            features=features,
            market_data=market_data
        )
        
        # Print formatted output
        print(formatted)
        
        # Return complete data
        return {
            'date': date,
            'ticker': self.ticker,
            'strategy': strategy,
            'parameters': parameters,
            'features': features,
            'formatted_output': formatted,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Test the Recommendation Agent"""
    print("Testing Recommendation Agent...")
    print("=" * 70)
    
    # Create agent (local models for testing)
    agent = RecommendationAgent(ticker="SMH", use_s3=False)
    
    # Generate recommendation
    recommendation = agent.generate_recommendation()
    
    # Save to file
    output_file = f"recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(recommendation, f, indent=2, default=str)
    
    print(f"\n💾 Recommendation saved to {output_file}")


if __name__ == '__main__':
    main()
