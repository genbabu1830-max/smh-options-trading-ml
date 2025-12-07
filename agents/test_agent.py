#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Recommendation Agent
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.recommendation_agent import RecommendationAgent


def test_agent_initialization():
    """Test agent initialization"""
    print("\n" + "=" * 70)
    print("TEST 1: Agent Initialization")
    print("=" * 70)
    
    try:
        agent = RecommendationAgent(ticker="SMH", use_s3=False)
        print("✅ Agent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False


def test_fetch_market_data():
    """Test market data fetching"""
    print("\n" + "=" * 70)
    print("TEST 2: Fetch Market Data")
    print("=" * 70)
    
    try:
        agent = RecommendationAgent(ticker="SMH", use_s3=False)
        market_data = agent.fetch_market_data()
        
        print(f"✅ Market data fetched")
        print(f"   Ticker: {market_data.get('ticker')}")
        print(f"   Date: {market_data.get('date')}")
        print(f"   Current Price: ${market_data.get('current_price', 0):.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Market data fetch failed: {e}")
        return False


def test_feature_extraction():
    """Test feature extraction"""
    print("\n" + "=" * 70)
    print("TEST 3: Feature Extraction")
    print("=" * 70)
    
    try:
        agent = RecommendationAgent(ticker="SMH", use_s3=False)
        market_data = agent.fetch_market_data()
        features = agent.extract_features(market_data)
        
        print(f"✅ Features extracted")
        print(f"   Number of features: {len(features)}")
        print(f"   Sample features:")
        for key in list(features.keys())[:5]:
            print(f"      {key}: {features[key]}")
        
        return True
    except Exception as e:
        print(f"❌ Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_prediction():
    """Test strategy prediction"""
    print("\n" + "=" * 70)
    print("TEST 4: Strategy Prediction (Stage 1 - ML)")
    print("=" * 70)
    
    try:
        agent = RecommendationAgent(ticker="SMH", use_s3=False)
        market_data = agent.fetch_market_data()
        features = agent.extract_features(market_data)
        strategy = agent.predict_strategy(features)
        
        print(f"✅ Strategy predicted")
        print(f"   Strategy: {strategy['strategy']}")
        print(f"   Confidence: {strategy['confidence']:.1%}")
        print(f"   Model Accuracy: {strategy['model_accuracy']:.1%}")
        print(f"   Alternatives:")
        for alt in strategy['alternatives'][:3]:
            print(f"      {alt['strategy']}: {alt['confidence']:.1%}")
        
        return True
    except Exception as e:
        print(f"❌ Strategy prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parameter_generation():
    """Test parameter generation"""
    print("\n" + "=" * 70)
    print("TEST 5: Parameter Generation (Stage 2 - Rules)")
    print("=" * 70)
    
    try:
        agent = RecommendationAgent(ticker="SMH", use_s3=False)
        market_data = agent.fetch_market_data()
        features = agent.extract_features(market_data)
        strategy = agent.predict_strategy(features)
        parameters = agent.generate_parameters(
            strategy=strategy['strategy'],
            market_data=market_data,
            features=features
        )
        
        print(f"✅ Parameters generated")
        print(f"   Strategy: {strategy['strategy']}")
        print(f"   Parameters:")
        for key, value in list(parameters.items())[:10]:
            print(f"      {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ Parameter generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_recommendation():
    """Test full recommendation generation"""
    print("\n" + "=" * 70)
    print("TEST 6: Full Recommendation Generation")
    print("=" * 70)
    
    try:
        agent = RecommendationAgent(ticker="SMH", use_s3=False)
        recommendation = agent.generate_recommendation()
        
        print(f"✅ Full recommendation generated")
        print(f"   Date: {recommendation['date']}")
        print(f"   Ticker: {recommendation['ticker']}")
        print(f"   Strategy: {recommendation['strategy']['strategy']}")
        print(f"   Confidence: {recommendation['strategy']['confidence']:.1%}")
        
        return True
    except Exception as e:
        print(f"❌ Full recommendation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("RECOMMENDATION AGENT TEST SUITE")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Fetch Market Data", test_fetch_market_data),
        ("Feature Extraction", test_feature_extraction),
        ("Strategy Prediction", test_strategy_prediction),
        ("Parameter Generation", test_parameter_generation),
        ("Full Recommendation", test_full_recommendation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
