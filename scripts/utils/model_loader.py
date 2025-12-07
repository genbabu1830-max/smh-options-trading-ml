"""
Model Loader - Load ML Models from Local or S3
===============================================

Supports:
- Local loading (for development/testing)
- S3 loading (for production Lambda)
- Multi-asset support (ETF-specific, universal stock model)
- Efficient caching

Usage:
    from scripts.utils.model_loader import ModelLoader
    
    # Local loading
    loader = ModelLoader(source='local', base_path='models_storage')
    models = loader.load_models_for_ticker('SMH')
    
    # S3 loading
    loader = ModelLoader(source='s3', bucket_name='options-trading-models')
    models = loader.load_models_for_ticker('SMH')
"""

import os
import json
import joblib
from typing import Dict, Any, Optional, Literal
import warnings

# Optional S3 support
try:
    import boto3
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    warnings.warn("boto3 not installed. S3 loading will not be available.")


class ModelLoader:
    """
    Load ML models from local filesystem or S3.
    
    Architecture:
    - ETFs: Each ETF has its own dedicated model
    - Stocks: All stocks share one universal model
    """
    
    def __init__(
        self,
        source: Literal['local', 's3'] = 'local',
        base_path: str = 'models_storage',
        bucket_name: Optional[str] = None,
        environment: str = 'production'
    ):
        """
        Initialize model loader.
        
        Args:
            source: 'local' or 's3'
            base_path: Local base path (for local source)
            bucket_name: S3 bucket name (for s3 source)
            environment: production, staging, or archive/v1.0
        """
        self.source = source
        self.base_path = base_path
        self.bucket_name = bucket_name
        self.environment = environment
        
        # In-memory cache
        self._model_cache = {}
        
        # Initialize S3 client if needed
        if source == 's3':
            if not S3_AVAILABLE:
                raise ImportError("boto3 required for S3 loading. Install: pip install boto3")
            if not bucket_name:
                raise ValueError("bucket_name required for S3 source")
            self.s3 = boto3.client('s3')
        
        # Load asset registry
        self.asset_registry = self._load_asset_registry()
    
    def _load_asset_registry(self) -> Dict:
        """Load asset registry from local or S3."""
        try:
            if self.source == 'local':
                registry_path = os.path.join(self.base_path, 'metadata', 'asset_registry.json')
                with open(registry_path, 'r') as f:
                    return json.load(f)
            else:  # s3
                response = self.s3.get_object(
                    Bucket=self.bucket_name,
                    Key='metadata/asset_registry.json'
                )
                return json.loads(response['Body'].read())
        except Exception as e:
            warnings.warn(f"Could not load asset registry: {e}")
            return {"etfs": {}, "stocks": {}}
    
    def get_model_path_for_ticker(self, ticker: str) -> str:
        """
        Determine correct model path based on ticker.
        
        Args:
            ticker: Asset ticker (e.g., 'SMH', 'AAPL')
        
        Returns:
            Path prefix for model files
        
        Examples:
            'SMH' → 'etfs/SMH/production/'
            'AAPL' → 'stocks/universal/production/'
        """
        # Check if it's an ETF (each ETF has its own model)
        if ticker in self.asset_registry.get('etfs', {}):
            etf_info = self.asset_registry['etfs'][ticker]
            return etf_info.get('model_path', f'etfs/{ticker}/{self.environment}/')
        
        # Check if it's a stock (all stocks use universal model)
        stocks_info = self.asset_registry.get('stocks', {})
        supported_stocks = stocks_info.get('supported_tickers', {})
        
        if ticker in supported_stocks:
            # All stocks use the universal stock model
            model_info = stocks_info.get('model_info', {})
            return model_info.get('model_path', f'stocks/universal/{self.environment}/')
        
        # Default: assume it's an ETF
        warnings.warn(f"Ticker {ticker} not in registry, assuming ETF")
        return f'etfs/{ticker}/{self.environment}/'
    
    def _load_file_local(self, file_path: str) -> Any:
        """Load file from local filesystem."""
        full_path = os.path.join(self.base_path, file_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        
        if file_path.endswith('.json'):
            with open(full_path, 'r') as f:
                return json.load(f)
        elif file_path.endswith('.pkl'):
            return joblib.load(full_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
    
    def _load_file_s3(self, file_path: str) -> Any:
        """Load file from S3."""
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            file_bytes = response['Body'].read()
            
            if file_path.endswith('.json'):
                return json.loads(file_bytes)
            elif file_path.endswith('.pkl'):
                # Use BytesIO for joblib.load
                from io import BytesIO
                return joblib.load(BytesIO(file_bytes))
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
        except Exception as e:
            raise FileNotFoundError(f"Could not load from S3: {file_path}. Error: {e}")
    
    def load_file(self, file_path: str, use_cache: bool = True) -> Any:
        """
        Load file from local or S3 with caching.
        
        Args:
            file_path: Relative path to file
            use_cache: Whether to use cache
        
        Returns:
            Loaded object
        """
        # Check cache
        if use_cache and file_path in self._model_cache:
            return self._model_cache[file_path]
        
        # Load from source
        if self.source == 'local':
            obj = self._load_file_local(file_path)
        else:  # s3
            obj = self._load_file_s3(file_path)
        
        # Cache it
        if use_cache:
            self._model_cache[file_path] = obj
        
        return obj
    
    def load_models_for_ticker(self, ticker: str) -> Dict[str, Any]:
        """
        Load all models for a specific ticker.
        
        Args:
            ticker: Asset ticker (e.g., 'SMH', 'AAPL')
        
        Returns:
            Dictionary with all models for this ticker
        
        Examples:
            load_models_for_ticker('SMH')  # Loads SMH-specific model
            load_models_for_ticker('AAPL') # Loads universal stock model
            load_models_for_ticker('TSLA') # Loads same universal stock model (cached)
        """
        # Get correct model path
        model_path = self.get_model_path_for_ticker(ticker)
        
        print(f"Loading models for {ticker} from {model_path}")
        
        # Load models (will use cache if already loaded)
        models = {
            'ml_model': self.load_file(f'{model_path}lightgbm_clean_model.pkl'),
            'label_encoder': self.load_file(f'{model_path}label_encoder_clean.pkl'),
            'feature_names': self.load_file(f'{model_path}feature_names_clean.json'),
            'metadata': self.load_file(f'{model_path}metadata.json'),
            'ticker': ticker,
            'model_path': model_path
        }
        
        # Determine model type
        if 'etfs/' in model_path:
            models['model_type'] = 'etf_specific'
        elif 'stocks/universal' in model_path:
            models['model_type'] = 'stock_universal'
        else:
            models['model_type'] = 'unknown'
        
        print(f"✅ Loaded {models['model_type']} model for {ticker}")
        print(f"   Model version: {models['metadata'].get('version', 'unknown')}")
        print(f"   Accuracy: {models['metadata'].get('accuracy', 0):.2%}")
        
        return models
    
    def clear_cache(self):
        """Clear in-memory cache."""
        self._model_cache.clear()
        print("✅ Cache cleared")
    
    def get_cache_info(self) -> Dict:
        """Get information about cached models."""
        return {
            'cached_files': list(self._model_cache.keys()),
            'cache_size': len(self._model_cache),
            'source': self.source
        }


# Example usage
if __name__ == "__main__":
    print("Model Loader - Multi-Asset Support")
    print("=" * 60)
    
    # Test local loading
    print("\n1. Testing Local Loading:")
    print("-" * 60)
    
    try:
        loader = ModelLoader(source='local', base_path='models_storage')
        
        # Load SMH model
        smh_models = loader.load_models_for_ticker('SMH')
        print(f"\nSMH Model Info:")
        print(f"  Type: {smh_models['model_type']}")
        print(f"  Path: {smh_models['model_path']}")
        print(f"  Features: {len(smh_models['feature_names'])}")
        
        # Show cache info
        cache_info = loader.get_cache_info()
        print(f"\nCache Info:")
        print(f"  Cached files: {cache_info['cache_size']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Usage Examples:")
    print("-" * 60)
    print("""
# Local loading (development)
loader = ModelLoader(source='local', base_path='models_storage')
models = loader.load_models_for_ticker('SMH')

# S3 loading (production)
loader = ModelLoader(source='s3', bucket_name='options-trading-models')
models = loader.load_models_for_ticker('SMH')

# Use the model
prediction = models['ml_model'].predict(features)
strategy = models['label_encoder'].inverse_transform(prediction)[0]
    """)
