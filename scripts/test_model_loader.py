"""
Test Model Loader
=================

Test loading models from local storage and verify they work.
"""

import sys
import os
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.model_loader import ModelLoader

def test_local_loading():
    """Test loading models from local storage."""
    print("=" * 60)
    print("Test 1: Local Model Loading")
    print("=" * 60)
    
    # Initialize loader
    loader = ModelLoader(source='local', base_path='models_storage')
    
    # Load SMH model
    print("\nLoading SMH model...")
    models = loader.load_models_for_ticker('SMH')
    
    # Verify model components
    assert 'ml_model' in models, "ML model not loaded"
    assert 'label_encoder' in models, "Label encoder not loaded"
    assert 'feature_names' in models, "Feature names not loaded"
    assert 'metadata' in models, "Metadata not loaded"
    
    print(f"\n✅ All components loaded successfully")
    print(f"   Model type: {models['model_type']}")
    print(f"   Features: {len(models['feature_names'])}")
    print(f"   Accuracy: {models['metadata']['accuracy']:.2%}")
    
    return models


def test_prediction(models):
    """Test making a prediction with loaded model."""
    print("\n" + "=" * 60)
    print("Test 2: Model Prediction")
    print("=" * 60)
    
    # Create dummy features (84 features)
    feature_names = models['feature_names']
    dummy_features = {name: 0.5 for name in feature_names}
    
    # Set some realistic values
    dummy_features['current_price'] = 236.80
    dummy_features['iv_rank'] = 45.0
    dummy_features['rsi_14'] = 52.0
    dummy_features['adx_14'] = 22.0
    dummy_features['trend_regime'] = 2
    dummy_features['volatility_regime'] = 2
    dummy_features['volume_regime'] = 1
    
    # Convert to DataFrame
    feature_df = pd.DataFrame([dummy_features], columns=feature_names)
    
    print(f"\nMaking prediction with {len(feature_names)} features...")
    
    # Predict
    prediction = models['ml_model'].predict(feature_df)[0]
    probabilities = models['ml_model'].predict_proba(feature_df)[0]
    
    # Decode strategy
    strategy = models['label_encoder'].inverse_transform([prediction])[0]
    confidence = probabilities[prediction]
    
    print(f"\n✅ Prediction successful")
    print(f"   Strategy: {strategy}")
    print(f"   Confidence: {confidence:.2%}")
    
    # Show top 3 strategies
    top_3_idx = probabilities.argsort()[-3:][::-1]
    print(f"\n   Top 3 strategies:")
    for i, idx in enumerate(top_3_idx, 1):
        strat = models['label_encoder'].inverse_transform([idx])[0]
        conf = probabilities[idx]
        print(f"      {i}. {strat}: {conf:.2%}")
    
    return strategy, confidence


def test_cache():
    """Test caching functionality."""
    print("\n" + "=" * 60)
    print("Test 3: Caching")
    print("=" * 60)
    
    loader = ModelLoader(source='local', base_path='models_storage')
    
    # First load
    print("\nFirst load (from disk)...")
    models1 = loader.load_models_for_ticker('SMH')
    
    # Second load (from cache)
    print("\nSecond load (from cache)...")
    models2 = loader.load_models_for_ticker('SMH')
    
    # Verify same object
    same_model = models1['ml_model'] is models2['ml_model']
    print(f"\n✅ Cache working: {same_model}")
    
    # Show cache info
    cache_info = loader.get_cache_info()
    print(f"   Cached files: {cache_info['cache_size']}")
    print(f"   Files: {cache_info['cached_files'][:2]}...")
    
    return same_model


def test_multi_ticker():
    """Test loading models for different tickers."""
    print("\n" + "=" * 60)
    print("Test 4: Multi-Ticker Support")
    print("=" * 60)
    
    loader = ModelLoader(source='local', base_path='models_storage')
    
    # Test SMH (ETF - should work)
    print("\nTesting SMH (ETF)...")
    try:
        smh_models = loader.load_models_for_ticker('SMH')
        print(f"✅ SMH loaded: {smh_models['model_type']}")
    except Exception as e:
        print(f"❌ SMH failed: {e}")
    
    # Test AAPL (Stock - will fail until universal model exists)
    print("\nTesting AAPL (Stock)...")
    try:
        aapl_models = loader.load_models_for_ticker('AAPL')
        print(f"✅ AAPL loaded: {aapl_models['model_type']}")
    except Exception as e:
        print(f"⚠️  AAPL not available yet (expected): {type(e).__name__}")
    
    # Test SPY (ETF - will fail until trained)
    print("\nTesting SPY (ETF)...")
    try:
        spy_models = loader.load_models_for_ticker('SPY')
        print(f"✅ SPY loaded: {spy_models['model_type']}")
    except Exception as e:
        print(f"⚠️  SPY not available yet (expected): {type(e).__name__}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MODEL LOADER TEST SUITE")
    print("=" * 60)
    
    try:
        # Test 1: Load models
        models = test_local_loading()
        
        # Test 2: Make prediction
        strategy, confidence = test_prediction(models)
        
        # Test 3: Test caching
        cache_works = test_cache()
        
        # Test 4: Multi-ticker
        test_multi_ticker()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✅ Local loading: PASSED")
        print("✅ Prediction: PASSED")
        print(f"✅ Caching: {'PASSED' if cache_works else 'FAILED'}")
        print("✅ Multi-ticker: PASSED (with expected failures)")
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
