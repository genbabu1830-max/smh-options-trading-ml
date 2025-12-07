# Models Storage Directory

This directory mirrors the S3 bucket structure for ML models.

## Structure

```
models_storage/
├── etfs/                    # ETF-specific models
│   ├── SMH/                # Semiconductor ETF
│   │   └── production/
│   │       ├── lightgbm_clean_model.pkl
│   │       ├── label_encoder_clean.pkl
│   │       ├── feature_names_clean.json
│   │       └── metadata.json
│   ├── SPY/                # S&P 500 ETF (planned)
│   ├── QQQ/                # Nasdaq 100 ETF (planned)
│   └── IWM/                # Russell 2000 ETF (planned)
│
├── stocks/                  # Universal stock model
│   └── universal/
│       └── production/
│           ├── lightgbm_model.pkl (planned)
│           ├── label_encoder.pkl (planned)
│           ├── feature_names.json (planned)
│           └── metadata.json (planned)
│
├── shared/                  # Shared components
│   ├── feature_extractors/
│   ├── scalers/
│   └── encoders/
│
└── metadata/
    └── asset_registry.json  # Registry of all assets
```

## Current Status

### Active Models
- ✅ **SMH (Semiconductor ETF)**: Production ready
  - Model: LightGBM
  - Accuracy: 84.21%
  - Features: 84
  - Strategies: 10

### Planned Models
- ⏳ **SPY**: S&P 500 ETF
- ⏳ **QQQ**: Nasdaq 100 ETF
- ⏳ **IWM**: Russell 2000 ETF
- ⏳ **Universal Stock Model**: For AAPL, TSLA, NVDA, etc.

## Usage

### Local Development

```python
from scripts.utils.model_loader import ModelLoader

# Load models locally
loader = ModelLoader(source='local', base_path='models_storage')
models = loader.load_models_for_ticker('SMH')

# Use the model
prediction = models['ml_model'].predict(features)
strategy = models['label_encoder'].inverse_transform(prediction)[0]
```

### Production (S3)

```python
from scripts.utils.model_loader import ModelLoader

# Load models from S3
loader = ModelLoader(source='s3', bucket_name='options-trading-models')
models = loader.load_models_for_ticker('SMH')
```

## Uploading to S3

```bash
# Dry run (see what would be uploaded)
python scripts/upload_models_to_s3.py --dry-run

# Upload to S3
python scripts/upload_models_to_s3.py --bucket options-trading-models

# Upload to specific region
python scripts/upload_models_to_s3.py --bucket options-trading-models --region us-west-2
```

## Adding New Models

### For a New ETF (e.g., SPY)

1. Create directory structure:
   ```bash
   mkdir -p models_storage/etfs/SPY/production
   ```

2. Train model and save files:
   ```python
   import joblib
   
   # Save model
   joblib.dump(model, 'models_storage/etfs/SPY/production/lightgbm_model.pkl')
   joblib.dump(encoder, 'models_storage/etfs/SPY/production/label_encoder.pkl')
   
   # Save metadata
   metadata = {
       "version": "1.0",
       "ticker": "SPY",
       "accuracy": 0.85,
       ...
   }
   with open('models_storage/etfs/SPY/production/metadata.json', 'w') as f:
       json.dump(metadata, f, indent=2)
   ```

3. Update asset registry:
   ```json
   {
     "etfs": {
       "SPY": {
         "name": "SPDR S&P 500 ETF",
         "model_path": "etfs/SPY/production/",
         "status": "active"
       }
     }
   }
   ```

4. Upload to S3:
   ```bash
   python scripts/upload_models_to_s3.py
   ```

### For Universal Stock Model

1. Create directory:
   ```bash
   mkdir -p models_storage/stocks/universal/production
   ```

2. Train on combined stock data (AAPL, TSLA, NVDA, etc.)

3. Save model files to `models_storage/stocks/universal/production/`

4. All stocks will automatically use this model

## File Sizes

| Model | Size | Description |
|-------|------|-------------|
| SMH LightGBM | 401 KB | Main prediction model |
| Label Encoder | 632 B | Strategy name encoder |
| Feature Names | 1.5 KB | List of 84 features |
| Metadata | <1 KB | Model information |

**Total per ETF:** ~403 KB

## Architecture Benefits

### ETF Models (Separate)
- Each ETF has unique characteristics
- Dedicated model captures ETF-specific patterns
- Better accuracy for each ETF

### Stock Models (Universal)
- Stocks share similar options behavior
- One model trained on all stocks
- Efficient: 1 model instead of 100+
- Easier to maintain and update

## Maintenance

### Retraining Models

```bash
# Retrain SMH model
python scripts/4_train_models.py --ticker SMH

# Copy to models_storage
cp models/lightgbm_clean_model.pkl models_storage/etfs/SMH/production/

# Upload to S3
python scripts/upload_models_to_s3.py
```

### Version Control

Models are versioned in metadata.json:
```json
{
  "version": "1.0",
  "created_date": "2024-12-06",
  "accuracy": 0.8421
}
```

Archive old versions:
```bash
mkdir -p models_storage/etfs/SMH/archive/v1.0
cp models_storage/etfs/SMH/production/* models_storage/etfs/SMH/archive/v1.0/
```

## Cost Estimate

### S3 Storage
- Per ETF: ~0.5 MB
- 10 ETFs: ~5 MB
- Universal stock model: ~0.5 MB
- **Total:** ~6 MB = $0.00014/month

### S3 Transfers
- Lambda downloads: ~10 cold starts/day
- 10 cold starts × 0.5 MB × 30 days = 150 MB/month
- **Cost:** $0.0015/month

**Total S3 Cost:** ~$0.002/month (essentially free!)

## Security

### IAM Policy for Lambda

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::options-trading-models",
        "arn:aws:s3:::options-trading-models/*"
      ]
    }
  ]
}
```

### Bucket Policy (Read-Only)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::options-trading-models/*"
    }
  ]
}
```

## Troubleshooting

### Model Not Found
```python
# Check asset registry
loader = ModelLoader(source='local')
print(loader.asset_registry)

# Check model path
path = loader.get_model_path_for_ticker('SMH')
print(f"Model path: {path}")
```

### Cache Issues
```python
# Clear cache
loader.clear_cache()

# Check cache
info = loader.get_cache_info()
print(f"Cached files: {info['cached_files']}")
```

### S3 Upload Fails
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check bucket exists
aws s3 ls s3://options-trading-models

# Test upload single file
aws s3 cp models_storage/metadata/asset_registry.json s3://options-trading-models/metadata/
```

## Next Steps

1. ✅ Set up local structure
2. ✅ Create ModelLoader
3. ✅ Create upload script
4. ⏳ Upload SMH model to S3
5. ⏳ Test S3 loading
6. ⏳ Train models for SPY, QQQ, IWM
7. ⏳ Train universal stock model
8. ⏳ Integrate with Strands agents
