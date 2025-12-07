# S3 Model Storage & Loading Guide
## Serverless ML Model Management for Options Trading Agent

**Date:** December 6, 2024  
**Purpose:** Store and efficiently load ML models from S3 for Lambda/serverless deployment

---

## Why S3 for Model Storage?

### Benefits

1. **Serverless Compatible** - Lambda has limited storage (512MB /tmp)
2. **Version Control** - Easy to manage multiple model versions
3. **Cost Effective** - Pay only for storage (~$0.023/GB/month)
4. **Fast Access** - Low latency from Lambda in same region
5. **Shared Access** - Multiple Lambda functions can use same models
6. **No Deployment Size Limits** - Lambda deployment package limited to 250MB, S3 has no such limit

### Cost Comparison

| Storage Method | Cost | Pros | Cons |
|----------------|------|------|------|
| **S3** | $0.023/GB/month | Cheap, scalable, versioned | Slight load time |
| **Lambda Layer** | Free (but limited) | Fast, no load time | 250MB limit, hard to update |
| **EFS** | $0.30/GB/month | Persistent | 13x more expensive |

**Our models:** ~50MB total → **$0.001/month on S3** ✅

---

## S3 Bucket Structure (Scalable Multi-Asset)

```
s3://options-trading-models/
│
├── etfs/                                  # ETF-specific models
│   ├── SMH/                              # Semiconductor ETF
│   │   ├── production/
│   │   │   ├── lightgbm_model.pkl        # 30MB - Main ML model
│   │   │   ├── label_encoder.pkl         # 1KB - Strategy encoder
│   │   │   ├── feature_names.json        # 5KB - Feature list
│   │   │   └── metadata.json             # Version, accuracy, date
│   │   ├── staging/
│   │   │   └── ...                       # Testing new models
│   │   └── archive/
│   │       ├── v1.0/
│   │       ├── v1.1/
│   │       └── v1.2/
│   │
│   ├── SPY/                              # S&P 500 ETF
│   │   ├── production/
│   │   ├── staging/
│   │   └── archive/
│   │
│   ├── QQQ/                              # Nasdaq 100 ETF
│   │   ├── production/
│   │   ├── staging/
│   │   └── archive/
│   │
│   ├── IWM/                              # Russell 2000 ETF
│   │   ├── production/
│   │   ├── staging/
│   │   └── archive/
│   │
│   └── XLF/                              # Financial Sector ETF
│       ├── production/
│       ├── staging/
│       └── archive/
│
├── stocks/                                # Universal stock model
│   ├── universal/                        # ONE model for ALL stocks
│   │   ├── production/
│   │   │   ├── lightgbm_model.pkl        # Universal stock model
│   │   │   ├── label_encoder.pkl
│   │   │   ├── feature_names.json
│   │   │   ├── stock_embeddings.pkl      # Stock-specific embeddings (optional)
│   │   │   └── metadata.json             # Trained on: AAPL, TSLA, NVDA, etc.
│   │   ├── staging/
│   │   └── archive/
│   │
│   └── training_data/                    # Combined training data
│       ├── AAPL_training.csv
│       ├── TSLA_training.csv
│       ├── NVDA_training.csv
│       ├── MSFT_training.csv
│       └── combined_stocks.csv           # All stocks merged
│
├── universal/                             # Universal models (optional future)
│   ├── all_assets_classifier/            # Universal model for ALL assets (ETFs + Stocks)
│   │   ├── production/
│   │   │   ├── universal_model.pkl       # Trained on everything
│   │   │   ├── asset_embeddings.pkl      # Asset-specific embeddings
│   │   │   ├── feature_names.json
│   │   │   └── metadata.json
│   │   ├── staging/
│   │   └── archive/
│   │
│   ├── volatility_predictor/             # Universal IV predictor (future)
│   │   ├── production/
│   │   ├── staging/
│   │   └── archive/
│   │
│   └── risk_scorer/                      # Universal risk assessment (future)
│       ├── production/
│       ├── staging/
│       └── archive/
│
├── shared/                                # Shared components across all models
│   ├── feature_extractors/
│   │   ├── base_extractor.pkl            # Base feature extraction logic
│   │   ├── technical_indicators.pkl      # Technical indicator calculator
│   │   └── options_metrics.pkl           # Options-specific metrics
│   │
│   ├── scalers/
│   │   ├── standard_scaler.pkl           # Feature scaling
│   │   └── robust_scaler.pkl             # Outlier-resistant scaling
│   │
│   └── encoders/
│       ├── strategy_encoder.pkl          # Universal strategy encoder
│       └── regime_encoder.pkl            # Market regime encoder
│
├── ensembles/                             # Ensemble models (combine multiple)
│   ├── multi_asset_ensemble/
│   │   ├── production/
│   │   │   ├── ensemble_weights.json     # Weights for each asset model
│   │   │   ├── voting_strategy.json      # How to combine predictions
│   │   │   └── metadata.json
│   │   └── archive/
│   │
│   └── sector_rotation_ensemble/
│       ├── production/
│       └── archive/
│
├── experimental/                          # Experimental models (not production)
│   ├── deep_learning/
│   │   ├── lstm_strategy_predictor/
│   │   └── transformer_model/
│   │
│   ├── reinforcement_learning/
│   │   └── rl_agent/
│   │
│   └── neural_architecture_search/
│       └── nas_models/
│
└── metadata/                              # Global metadata and configs
    ├── asset_registry.json               # List of all supported assets
    ├── model_registry.json               # All deployed models
    ├── performance_tracking.json         # Historical performance by asset
    └── deployment_history.json           # Deployment audit log
```

### Path Convention Examples

```python
# ETF-specific model (each ETF has its own model)
"etfs/SMH/production/lightgbm_model.pkl"
"etfs/SPY/production/lightgbm_model.pkl"
"etfs/QQQ/production/lightgbm_model.pkl"

# Universal stock model (ONE model for ALL stocks)
"stocks/universal/production/lightgbm_model.pkl"  # Works for AAPL, TSLA, NVDA, etc.

# Universal model for everything (optional future)
"universal/all_assets_classifier/production/universal_model.pkl"

# Shared component
"shared/feature_extractors/base_extractor.pkl"

# Ensemble combining multiple assets
"ensembles/multi_asset_ensemble/production/ensemble_weights.json"
```

### Metadata Structure

```json
// metadata/asset_registry.json
{
  "etfs": {
    "SMH": {
      "name": "VanEck Semiconductor ETF",
      "sector": "Technology",
      "model_type": "etf_specific",
      "model_path": "etfs/SMH/production/",
      "status": "active",
      "last_trained": "2024-12-06",
      "accuracy": 0.8421
    },
    "SPY": {
      "name": "SPDR S&P 500 ETF",
      "sector": "Broad Market",
      "model_type": "etf_specific",
      "model_path": "etfs/SPY/production/",
      "status": "planned"
    },
    "QQQ": {
      "name": "Invesco QQQ ETF",
      "sector": "Technology",
      "model_type": "etf_specific",
      "model_path": "etfs/QQQ/production/",
      "status": "planned"
    }
  },
  "stocks": {
    "model_info": {
      "type": "universal",
      "model_path": "stocks/universal/production/",
      "trained_on": ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN"],
      "status": "planned",
      "note": "ONE model handles ALL stocks"
    },
    "supported_tickers": {
      "AAPL": {
        "name": "Apple Inc.",
        "sector": "Technology",
        "uses_model": "stocks/universal"
      },
      "TSLA": {
        "name": "Tesla Inc.",
        "sector": "Automotive",
        "uses_model": "stocks/universal"
      },
      "NVDA": {
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "uses_model": "stocks/universal"
      }
    }
  }
}
```

---

## Implementation

### Step 1: Upload Models to S3

```python
# scripts/upload_models_to_s3.py

import boto3
import json
from datetime import datetime

def upload_models_to_s3():
    """Upload trained models to S3."""
    
    s3 = boto3.client('s3')
    bucket_name = 'smh-options-models'
    
    # Create bucket if doesn't exist
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"✅ Created bucket: {bucket_name}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"✅ Bucket already exists: {bucket_name}")
    
    # Files to upload
    files_to_upload = [
        {
            'local': 'models/lightgbm_clean_model.pkl',
            's3_key': 'production/lightgbm_clean_model.pkl',
            'description': 'Main LightGBM model for strategy prediction'
        },
        {
            'local': 'models/label_encoder_clean.pkl',
            's3_key': 'production/label_encoder_clean.pkl',
            'description': 'Label encoder for strategy names'
        },
        {
            'local': 'models/feature_names_clean.json',
            's3_key': 'production/feature_names_clean.json',
            'description': 'List of 84 feature names'
        }
    ]
    
    # Upload each file
    for file_info in files_to_upload:
        print(f"\nUploading {file_info['local']}...")
        
        s3.upload_file(
            Filename=file_info['local'],
            Bucket=bucket_name,
            Key=file_info['s3_key'],
            ExtraArgs={
                'Metadata': {
                    'description': file_info['description'],
                    'upload_date': datetime.now().isoformat()
                }
            }
        )
        
        # Get file size
        response = s3.head_object(Bucket=bucket_name, Key=file_info['s3_key'])
        size_mb = response['ContentLength'] / (1024 * 1024)
        
        print(f"✅ Uploaded: s3://{bucket_name}/{file_info['s3_key']}")
        print(f"   Size: {size_mb:.2f} MB")
    
    # Create metadata file
    metadata = {
        'version': '1.0',
        'created_date': datetime.now().isoformat(),
        'model_type': 'LightGBM',
        'accuracy': 0.8421,
        'training_samples': 216,
        'features': 84,
        'strategies': 10,
        'files': {
            'model': 'production/lightgbm_clean_model.pkl',
            'encoder': 'production/label_encoder_clean.pkl',
            'features': 'production/feature_names_clean.json'
        }
    }
    
    s3.put_object(
        Bucket=bucket_name,
        Key='production/model_metadata.json',
        Body=json.dumps(metadata, indent=2),
        ContentType='application/json'
    )
    
    print(f"\n✅ All models uploaded successfully!")
    print(f"   Bucket: s3://{bucket_name}/production/")
    
    return bucket_name


if __name__ == "__main__":
    upload_models_to_s3()
```

**Run it:**
```bash
python scripts/upload_models_to_s3.py
```

---

### Step 2: Load Models from S3 (Multi-Asset Support)

```python
# agents/model_loader.py

import boto3
import joblib
import json
import os
from io import BytesIO
from typing import Dict, Any, Optional

class ModelLoader:
    """
    Efficient model loader with caching for Lambda.
    
    Features:
    - Lazy loading (load only when needed)
    - In-memory caching (reuse across Lambda invocations)
    - /tmp caching (persist across warm starts)
    - Automatic retry on failure
    """
    
    def __init__(self, bucket_name: str = 'options-trading-models', 
                 environment: str = 'production'):
        """
        Initialize model loader with multi-asset support.
        
        Args:
            bucket_name: S3 bucket name
            environment: production, staging, or archive/v1.0
        """
        self.bucket_name = bucket_name
        self.environment = environment
        self.s3 = boto3.client('s3')
        
        # In-memory cache (persists across Lambda warm starts)
        self._model_cache = {}
        
        # /tmp cache directory (Lambda has 512MB /tmp)
        self.cache_dir = '/tmp/models'
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load asset registry
        self.asset_registry = self._load_asset_registry()
    
    def load_model(self, model_name: str, use_cache: bool = True) -> Any:
        """
        Load model from S3 with caching.
        
        Args:
            model_name: Model filename (e.g., 'lightgbm_clean_model.pkl')
            use_cache: Whether to use cache
        
        Returns:
            Loaded model object
        """
        cache_key = f"{self.environment}/{model_name}"
        
        # Check in-memory cache first (fastest)
        if use_cache and cache_key in self._model_cache:
            print(f"✅ Loaded {model_name} from memory cache")
            return self._model_cache[cache_key]
        
        # Check /tmp cache (fast)
        tmp_path = os.path.join(self.cache_dir, model_name)
        if use_cache and os.path.exists(tmp_path):
            print(f"✅ Loading {model_name} from /tmp cache")
            with open(tmp_path, 'rb') as f:
                model = joblib.load(f)
            self._model_cache[cache_key] = model
            return model
        
        # Load from S3 (slower, but only happens once)
        print(f"📥 Downloading {model_name} from S3...")
        s3_key = f"{self.environment}/{model_name}"
        
        try:
            # Download to memory
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            model_bytes = response['Body'].read()
            size_mb = len(model_bytes) / (1024 * 1024)
            print(f"   Downloaded {size_mb:.2f} MB")
            
            # Load model
            model = joblib.loads(model_bytes)
            
            # Cache in memory
            self._model_cache[cache_key] = model
            
            # Cache in /tmp for next invocation
            with open(tmp_path, 'wb') as f:
                f.write(model_bytes)
            
            print(f"✅ Loaded and cached {model_name}")
            return model
            
        except Exception as e:
            print(f"❌ Error loading {model_name}: {e}")
            raise
    
    def load_json(self, filename: str) -> Dict:
        """Load JSON file from S3."""
        s3_key = f"{self.environment}/{filename}"
        
        response = self.s3.get_object(
            Bucket=self.bucket_name,
            Key=s3_key
        )
        
        return json.loads(response['Body'].read())
    
    def load_all_models(self) -> Dict[str, Any]:
        """
        Load all required models at once.
        
        Returns:
            Dictionary with all models
        """
        print("Loading all models from S3...")
        
        models = {
            'ml_model': self.load_model('lightgbm_clean_model.pkl'),
            'label_encoder': self.load_model('label_encoder_clean.pkl'),
            'feature_names': self.load_json('feature_names_clean.json'),
            'metadata': self.load_json('model_metadata.json')
        }
        
        print(f"✅ All models loaded (version {models['metadata']['version']})")
        return models
    
    def clear_cache(self):
        """Clear in-memory cache (useful for testing)."""
        self._model_cache.clear()
        print("✅ Cache cleared")
    
    def _load_asset_registry(self) -> Dict:
        """Load asset registry from S3."""
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key='metadata/asset_registry.json'
            )
            return json.loads(response['Body'].read())
        except Exception as e:
            print(f"⚠️ Could not load asset registry: {e}")
            return {"etfs": {}, "stocks": {}}
    
    def get_model_path_for_ticker(self, ticker: str) -> str:
        """
        Determine correct model path based on ticker.
        
        Args:
            ticker: Asset ticker (e.g., 'SMH', 'AAPL')
        
        Returns:
            S3 path prefix for model files
        
        Examples:
            'SMH' → 'etfs/SMH/production/'
            'AAPL' → 'stocks/universal/production/'
            'TSLA' → 'stocks/universal/production/'
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
        print(f"⚠️ Ticker {ticker} not in registry, assuming ETF")
        return f'etfs/{ticker}/{self.environment}/'
    
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
            'ml_model': self.load_model(f'{model_path}lightgbm_model.pkl'),
            'label_encoder': self.load_model(f'{model_path}label_encoder.pkl'),
            'feature_names': self.load_json(f'{model_path}feature_names.json'),
            'metadata': self.load_json(f'{model_path}metadata.json'),
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
        return models


# Global instance (reused across Lambda invocations)
_model_loader = None

def get_model_loader() -> ModelLoader:
    """Get or create global model loader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
```

---

### Step 3: Use in Recommendation Agent (Multi-Asset)

```python
# agents/recommendation_agent.py

from strands import Agent, tool
from strands.models import BedrockModel
from agents.model_loader import get_model_loader
from scripts.utils.feature_extractor import FeatureExtractor
from scripts.utils.parameter_generator import ParameterGenerator, RiskManager

# Initialize components (loaded once, reused)
feature_extractor = FeatureExtractor()
risk_manager = RiskManager(account_size=10000, risk_per_trade=0.02)
parameter_generator = ParameterGenerator(risk_manager=risk_manager)

# Get model loader (global instance)
model_loader = get_model_loader()


@tool
def predict_strategy(ticker: str, features: dict) -> dict:
    """
    Use ML model to predict optimal options strategy.
    Automatically loads correct model based on ticker.
    
    Args:
        ticker: Asset ticker (e.g., 'SMH', 'AAPL')
        features: Dictionary with 84 features
    
    Returns:
        Strategy prediction with confidence
    
    Examples:
        predict_strategy('SMH', features)   # Uses SMH-specific model
        predict_strategy('AAPL', features)  # Uses universal stock model
        predict_strategy('TSLA', features)  # Uses same universal stock model (cached)
    """
    # Load models for this ticker (uses cache if already loaded)
    models = model_loader.load_models_for_ticker(ticker)
    
    ml_model = models['ml_model']
    label_encoder = models['label_encoder']
    
    # Convert features to DataFrame
    feature_df = feature_extractor.get_feature_dataframe(features)
    
    # Predict using cached model
    prediction = ml_model.predict(feature_df)[0]
    probabilities = ml_model.predict_proba(feature_df)[0]
    
    # Decode strategy
    strategy = label_encoder.inverse_transform([prediction])[0]
    confidence = float(probabilities[prediction])
    
    return {
        'ticker': ticker,
        'strategy': strategy,
        'confidence': confidence,
        'model_type': models['model_type'],
        'model_path': models['model_path'],
        'model_version': models['metadata'].get('version', '1.0'),
        'model_accuracy': models['metadata'].get('accuracy', 0.0)
    }


# Create agent
recommendation_agent = Agent(
    model=BedrockModel(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        temperature=0.1,
        region_name="us-east-1"
    ),
    tools=[predict_strategy, ...],
    system_prompt="""
    You generate options trade recommendations for multiple assets.
    
    Supported Assets:
    - ETFs: SMH, SPY, QQQ (each has dedicated model)
    - Stocks: AAPL, TSLA, NVDA, etc. (all use universal model)
    
    Always specify the ticker when calling predict_strategy.
    """
)
```

---

### Step 4: Lambda Handler with S3 Models

```python
# lambda/recommendation_handler.py

import json
from datetime import datetime
from agents.recommendation_agent import recommendation_agent

def lambda_handler(event, context):
    """
    Lambda handler for options recommendation.
    Models are loaded from S3 on cold start, then cached.
    """
    
    print(f"Lambda invocation started")
    print(f"Request ID: {context.request_id}")
    print(f"Memory limit: {context.memory_limit_in_mb} MB")
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        ticker = body.get('ticker', 'SMH')
        date = body.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        print(f"Generating recommendation for {ticker} on {date}")
        
        # Generate recommendation (models loaded from S3 if not cached)
        response = recommendation_agent(
            f"Generate options trade recommendation for {ticker} on {date}"
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'recommendation': response,
                'timestamp': datetime.now().isoformat(),
                'request_id': context.request_id
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'request_id': context.request_id
            })
        }
```

---

## Multi-Asset Model Loading Examples

### Example 1: ETF Trading (Separate Models)

```python
# Each ETF loads its own model
model_loader = get_model_loader()

# Load SMH model
smh_models = model_loader.load_models_for_ticker('SMH')
# Downloads from: etfs/SMH/production/lightgbm_model.pkl

# Load SPY model  
spy_models = model_loader.load_models_for_ticker('SPY')
# Downloads from: etfs/SPY/production/lightgbm_model.pkl

# Load QQQ model
qqq_models = model_loader.load_models_for_ticker('QQQ')
# Downloads from: etfs/QQQ/production/lightgbm_model.pkl

print(f"SMH model type: {smh_models['model_type']}")  # etf_specific
print(f"SPY model type: {spy_models['model_type']}")  # etf_specific
```

### Example 2: Stock Trading (Universal Model)

```python
# All stocks use the SAME universal model (efficient!)
model_loader = get_model_loader()

# Load for AAPL
aapl_models = model_loader.load_models_for_ticker('AAPL')
# Downloads from: stocks/universal/production/lightgbm_model.pkl

# Load for TSLA (uses cached model - no download!)
tsla_models = model_loader.load_models_for_ticker('TSLA')
# Uses cached: stocks/universal/production/lightgbm_model.pkl

# Load for NVDA (uses cached model - no download!)
nvda_models = model_loader.load_models_for_ticker('NVDA')
# Uses cached: stocks/universal/production/lightgbm_model.pkl

print(f"AAPL model type: {aapl_models['model_type']}")  # stock_universal
print(f"TSLA model type: {tsla_models['model_type']}")  # stock_universal
print(f"Same model? {aapl_models['ml_model'] is tsla_models['ml_model']}")  # True!
```

### Example 3: Mixed Portfolio

```python
# Trading both ETFs and stocks
model_loader = get_model_loader()

# ETF: SMH (dedicated model)
smh_prediction = predict_strategy('SMH', smh_features)
# Uses: etfs/SMH/production/lightgbm_model.pkl

# Stock: AAPL (universal model)
aapl_prediction = predict_strategy('AAPL', aapl_features)
# Uses: stocks/universal/production/lightgbm_model.pkl

# Stock: TSLA (same universal model, cached)
tsla_prediction = predict_strategy('TSLA', tsla_features)
# Uses: stocks/universal/production/lightgbm_model.pkl (cached)

# ETF: SPY (dedicated model)
spy_prediction = predict_strategy('SPY', spy_features)
# Uses: etfs/SPY/production/lightgbm_model.pkl

# Result: 3 models loaded (SMH, SPY, stocks/universal)
# AAPL and TSLA share the same model (efficient!)
```

### Caching Benefits

**Without Universal Stock Model:**
- 100 stocks = 100 model downloads = ~3GB
- Cold start: 60+ seconds
- Memory: Exceeds Lambda limits

**With Universal Stock Model:**
- 100 stocks = 1 model download = ~30MB
- Cold start: 2-3 seconds
- Memory: Well within limits ✅

---

## Performance Optimization

### Cold Start vs Warm Start

**Cold Start (First invocation):**
```
1. Lambda container starts: ~1-2 seconds
2. Import libraries: ~2-3 seconds
3. Load models from S3: ~1-2 seconds (30MB)
4. Execute recommendation: ~0.5 seconds
Total: ~5-8 seconds
```

**Warm Start (Subsequent invocations):**
```
1. Models already in memory: 0 seconds
2. Execute recommendation: ~0.5 seconds
Total: ~0.5 seconds ✅
```

### Optimization Strategies

#### 1. **Lazy Loading** (Load only what you need)

```python
class LazyModelLoader:
    """Load models only when first accessed."""
    
    def __init__(self):
        self._ml_model = None
        self._label_encoder = None
    
    @property
    def ml_model(self):
        if self._ml_model is None:
            loader = get_model_loader()
            self._ml_model = loader.load_model('lightgbm_clean_model.pkl')
        return self._ml_model
    
    @property
    def label_encoder(self):
        if self._label_encoder is None:
            loader = get_model_loader()
            self._label_encoder = loader.load_model('label_encoder_clean.pkl')
        return self._label_encoder

# Use it
lazy_loader = LazyModelLoader()

@tool
def predict_strategy(features: dict) -> dict:
    # Model loaded only when first called
    prediction = lazy_loader.ml_model.predict(...)
    strategy = lazy_loader.label_encoder.inverse_transform(...)
    return {...}
```

#### 2. **Provisioned Concurrency** (Keep Lambda warm)

```python
# terraform/lambda.tf

resource "aws_lambda_function" "recommendation" {
  # ... other config
  
  # Keep 1 instance always warm
  reserved_concurrent_executions = 1
}

resource "aws_lambda_provisioned_concurrency_config" "recommendation" {
  function_name = aws_lambda_function.recommendation.function_name
  qualifier     = aws_lambda_alias.recommendation.name
  
  provisioned_concurrent_executions = 1  # Always 1 warm instance
}
```

**Cost:** ~$6/month for 1 always-warm instance (optional, only if cold starts are issue)

#### 3. **Compress Models** (Reduce S3 transfer time)

```python
# scripts/compress_models.py

import gzip
import joblib

def compress_model(input_path, output_path):
    """Compress model with gzip."""
    
    # Load model
    model = joblib.load(input_path)
    
    # Save compressed
    with gzip.open(output_path, 'wb') as f:
        joblib.dump(model, f, compress=('gzip', 3))
    
    # Compare sizes
    import os
    original_size = os.path.getsize(input_path) / (1024 * 1024)
    compressed_size = os.path.getsize(output_path) / (1024 * 1024)
    
    print(f"Original: {original_size:.2f} MB")
    print(f"Compressed: {compressed_size:.2f} MB")
    print(f"Savings: {(1 - compressed_size/original_size)*100:.1f}%")

# Compress
compress_model(
    'models/lightgbm_clean_model.pkl',
    'models/lightgbm_clean_model.pkl.gz'
)
```

**Load compressed:**
```python
import gzip

with gzip.open('model.pkl.gz', 'rb') as f:
    model = joblib.load(f)
```

---

## Versioning & Rollback

### Version Management

```python
# scripts/deploy_model_version.py

def deploy_model_version(version: str, promote_to_production: bool = False):
    """Deploy new model version to S3."""
    
    s3 = boto3.client('s3')
    bucket = 'smh-options-models'
    
    # Upload to versioned path
    s3.upload_file(
        'models/lightgbm_clean_model.pkl',
        bucket,
        f'archive/{version}/lightgbm_clean_model.pkl'
    )
    
    # Update metadata
    metadata = {
        'version': version,
        'deployed_date': datetime.now().isoformat(),
        'accuracy': 0.8421,
        'status': 'staging'
    }
    
    s3.put_object(
        Bucket=bucket,
        Key=f'archive/{version}/metadata.json',
        Body=json.dumps(metadata, indent=2)
    )
    
    # Promote to production if requested
    if promote_to_production:
        s3.copy_object(
            Bucket=bucket,
            CopySource=f'{bucket}/archive/{version}/lightgbm_clean_model.pkl',
            Key='production/lightgbm_clean_model.pkl'
        )
        print(f"✅ Version {version} promoted to production")
    else:
        print(f"✅ Version {version} deployed to staging")

# Deploy new version
deploy_model_version('v1.1', promote_to_production=False)

# Test in staging
# If good, promote
deploy_model_version('v1.1', promote_to_production=True)
```

### Rollback

```python
def rollback_to_version(version: str):
    """Rollback production to specific version."""
    
    s3 = boto3.client('s3')
    bucket = 'smh-options-models'
    
    # Copy archived version to production
    s3.copy_object(
        Bucket=bucket,
        CopySource=f'{bucket}/archive/{version}/lightgbm_clean_model.pkl',
        Key='production/lightgbm_clean_model.pkl'
    )
    
    print(f"✅ Rolled back to version {version}")

# Rollback if needed
rollback_to_version('v1.0')
```

---

## Monitoring & Alerts

### CloudWatch Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def log_model_load_time(duration_ms: float):
    """Log model load time to CloudWatch."""
    
    cloudwatch.put_metric_data(
        Namespace='OptionsTrading',
        MetricData=[{
            'MetricName': 'ModelLoadTime',
            'Value': duration_ms,
            'Unit': 'Milliseconds'
        }]
    )

# In model loader
import time

start = time.time()
model = load_model_from_s3()
duration = (time.time() - start) * 1000

log_model_load_time(duration)
```

### S3 Access Logs

```python
# Enable S3 access logging
s3.put_bucket_logging(
    Bucket='smh-options-models',
    BucketLoggingStatus={
        'LoggingEnabled': {
            'TargetBucket': 'smh-options-logs',
            'TargetPrefix': 'model-access/'
        }
    }
)
```

---

## Cost Analysis

### Storage Costs

| Item | Size | Cost/Month |
|------|------|------------|
| ML Model | 30 MB | $0.0007 |
| Label Encoder | 1 KB | $0.00002 |
| Feature Names | 5 KB | $0.0001 |
| Metadata | 1 KB | $0.00002 |
| **Total** | **~30 MB** | **$0.0008** |

### Transfer Costs

| Scenario | Transfers/Month | Data | Cost |
|----------|----------------|------|------|
| Cold starts | 10 | 300 MB | $0.003 |
| Warm starts | 610 | 0 MB | $0.00 |
| **Total** | **620** | **300 MB** | **$0.003** |

### Total S3 Cost: **~$0.004/month** ✅

---

## Summary

### ✅ Benefits of S3 Storage

1. **Cost:** $0.004/month (essentially free)
2. **Performance:** ~1-2 seconds cold start, instant warm start
3. **Scalability:** Unlimited storage, handles any model size
4. **Versioning:** Easy rollback and A/B testing
5. **Shared:** Multiple Lambda functions can use same models

### 📋 Implementation Checklist

- [ ] Create S3 bucket: `smh-options-models`
- [ ] Upload models with `upload_models_to_s3.py`
- [ ] Implement `ModelLoader` class with caching
- [ ] Update agent to use S3 models
- [ ] Test cold start performance
- [ ] Set up versioning and rollback
- [ ] Configure CloudWatch monitoring

### 🚀 Next Steps

1. Run upload script to push models to S3
2. Test model loading locally
3. Deploy to Lambda and test cold/warm starts
4. Monitor performance and optimize if needed

**Ready to implement!**

