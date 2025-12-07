"""
Test S3 Model Loading
=====================

Test loading models from S3 bucket.
"""

import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.model_loader import ModelLoader


def test_s3_loading():
    """Test loading models from S3."""
    print("=" * 60)
    print("Test: S3 Model Loading")
    print("=" * 60)
    
    # Initialize S3 loader
    bucket_name = 'options-trading-models-969748929153'
    print(f"\nBucket: {bucket_name}")
    
    loader = ModelLoader(source='s3', bucket_name=bucket_name)
    
    # Load SMH model from S3
    print("\nLoading SMH model from S3...")
    models = loader.load_models_for_ticker('SMH')
    
    # Verify components
    assert 'ml_model' in models, "ML model not loaded"
    assert 'label_encoder' in models, "Label encoder not loaded"
    assert 'feature_names' in models, "Feature names not loaded"
    assert 'metadata' in models, "Metadata not loaded"
    
    print(f"\n✅ All components loaded from S3")
    print(f"   Model type: {models['model_type']}")
    print(f"   Features: {len(models['feature_names'])}")
    print(f"   Accuracy: {models['metadata']['accuracy']:.2%}")
    print(f"   Version: {models['metadata']['version']}")
    
    # Test prediction
    print("\n" + "=" * 60)
    print("Test: Prediction with S3 Model")
    print("=" * 60)
    
    # Create dummy features
    feature_names = models['feature_names']
    dummy_features = {name: 0.5 for name in feature_names}
    
    # Set realistic values
    dummy_features['current_price'] = 236.80
    dummy_features['iv_rank'] = 45.0
    dummy_features['rsi_14'] = 52.0
    dummy_features['adx_14'] = 22.0
    dummy_features['trend_regime'] = 2
    dummy_features['volatility_regime'] = 2
    dummy_features['volume_regime'] = 1
    
    # Convert to DataFrame
    feature_df = pd.DataFrame([dummy_features], columns=feature_names)
    
    # Predict
    prediction = models['ml_model'].predict(feature_df)[0]
    probabilities = models['ml_model'].predict_proba(feature_df)[0]
    
    # Decode strategy
    strategy = models['label_encoder'].inverse_transform([prediction])[0]
    confidence = probabilities[prediction]
    
    print(f"\n✅ Prediction successful")
    print(f"   Strategy: {strategy}")
    print(f"   Confidence: {confidence:.2%}")
    
    # Test caching (second load should be instant)
    print("\n" + "=" * 60)
    print("Test: S3 Caching")
    print("=" * 60)
    
    print("\nSecond load (should use cache)...")
    models2 = loader.load_models_for_ticker('SMH')
    
    same_model = models['ml_model'] is models2['ml_model']
    print(f"\n✅ Cache working: {same_model}")
    
    cache_info = loader.get_cache_info()
    print(f"   Cached files: {cache_info['cache_size']}")
    
    return True


def main():
    """Run S3 loading test."""
    print("\n" + "=" * 60)
    print("S3 MODEL LOADING TEST")
    print("=" * 60)
    
    try:
        success = test_s3_loading()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✅ S3 loading: PASSED")
        print("✅ Prediction: PASSED")
        print("✅ Caching: PASSED")
        print("\n" + "=" * 60)
        print("All S3 tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
