# Workspace Structure - SMH Options Trading System

**Last Updated:** December 6, 2024  
**Version:** 2.0 (Enhanced)

---

## Root Directory

### Documentation Files
```
README.md                          # Main documentation
QUICK_START_ENHANCED.md            # Quick start guide (5 minutes)
ENHANCED_SYSTEM_COMPLETE.md        # Enhanced features documentation
TWO_STAGE_SYSTEM_COMPLETE.md       # System architecture
PRODUCTION_ARCHITECTURE.md         # Production deployment guide
SYSTEM_STATUS.md                   # Current system status
WORK_COMPLETED.md                  # Work completion summary
WORKSPACE_STRUCTURE.md             # This file
```

### Test Results
```
LIVE_PREDICTION_TEST_RESULTS.md    # Latest test results
FEATURE_EXTRACTION_COMPLETE.md     # Feature extraction validation
```

---

## Scripts Directory

### Core Utilities (`scripts/utils/`)
```
feature_extractor.py               # Stage 0: Feature extraction (789 lines)
parameter_generator.py             # Stage 2: Enhanced parameters (650 lines)
strategy_selector.py               # Strategy selection logic
advanced_features.py               # Advanced feature calculations
calculate_greeks.py                # Options Greeks calculations
```

### Test Scripts
```
test_enhanced_system.py            # Complete system integration test
7_predict_with_raw_data.py         # Raw data prediction
6_predict_strategy.py              # Strategy prediction
```

### Training Pipeline
```
2_engineer_features.py             # Feature engineering
3_create_labels.py                 # Label creation
4_train_models.py                  # Model training
5_fix_data_leakage.py              # Data leakage fixes
```

---

## Models Directory

### Trained Models
```
lightgbm_clean_model.pkl           # LightGBM model (84.21% accuracy)
label_encoder_clean.pkl            # Label encoder
feature_names_clean.json           # Feature names (84 features)
```

### Legacy Models
```
catboost_clean_model.pkl           # CatBoost model
lightgbm_model.pkl                 # Original LightGBM
catboost_model.pkl                 # Original CatBoost
```

---

## Data Directory

### Processed Data (`data/processed/`)
```
smh_training_data.csv              # Training dataset (248 days × 90 cols)
smh_training_data_clean.csv        # Cleaned training data
```

### Raw Data (`data/raw/`)
```
(Raw option chain data)
```

---

## Documentation Directory

### Technical Documentation
```
FEATURE_EXTRACTION_LAYER.md        # Feature extraction details
STRATEGY_SELECTION_RULES.md        # Strategy selection logic
model_prediction_input_output_guide.md  # Model I/O specifications
CRITICAL_FINDINGS.md               # Critical findings
DATASET_SUMMARY.md                 # Dataset statistics
DATA_STRUCTURE.md                  # Data structure details
massive_data_coverage_analysis.md  # Data coverage analysis
README.md                          # Documentation index
```

---

## Archive Directory

### Old Summaries (`archive/old_summaries/`)
```
COMPLETE_FLOW_TEST_SUCCESS.md      # Old test results
DATA_LEAKAGE_FIXED.md              # Data leakage fixes
INSTALL_ML_LIBRARIES.md            # Installation guide
MODEL_TRAINING_READY.md            # Training completion
PROJECT_SUMMARY.md                 # Old project summary
SYSTEM_COMPLETE.md                 # Old system status
```

### Phase Documents (`archive/phase_docs/`)
```
(Phase-specific documentation)
```

### Test Files (`archive/test_files/`)
```
test_complete_flow.py              # Old test script
```

---

## Configuration Files

### Kiro Settings (`.kiro/`)
```
.kiro/steering/
  ├── strategy-selection-rules.md  # Strategy selection standards
  ├── model-input-output-standards.md  # Model I/O requirements
  └── data-quality-standards.md    # Data quality standards
```

### Project Configuration
```
.gitignore                         # Git ignore rules
.env                               # Environment variables
setup_and_train.sh                 # Setup and training script
install_ml_simple.sh               # Simple ML installation
```

---

## Key Files by Purpose

### For Production Use
1. `scripts/utils/feature_extractor.py` - Extract features
2. `scripts/utils/parameter_generator.py` - Generate parameters
3. `models/lightgbm_clean_model.pkl` - ML model
4. `models/label_encoder_clean.pkl` - Label encoder
5. `README.md` - Main documentation

### For Testing
1. `scripts/test_enhanced_system.py` - Integration test
2. `QUICK_START_ENHANCED.md` - Quick start guide
3. `LIVE_PREDICTION_TEST_RESULTS.md` - Test results

### For Development
1. `scripts/2_engineer_features.py` - Feature engineering
2. `scripts/3_create_labels.py` - Label creation
3. `scripts/4_train_models.py` - Model training
4. `documentation/` - Technical docs

### For Understanding
1. `README.md` - Overview
2. `ENHANCED_SYSTEM_COMPLETE.md` - Enhanced features
3. `TWO_STAGE_SYSTEM_COMPLETE.md` - Architecture
4. `SYSTEM_STATUS.md` - Current status

---

## File Counts

### By Type
- Python scripts: 15
- Markdown docs: 25
- Model files: 7
- Data files: 2
- Config files: 5

### By Category
- Production code: 5 files
- Test code: 3 files
- Training code: 4 files
- Documentation: 25 files
- Models: 7 files

---

## Total Lines of Code

### Core System
- `feature_extractor.py`: 789 lines
- `parameter_generator.py`: 650 lines
- `test_enhanced_system.py`: 350 lines
- **Total: ~1,800 lines**

### Training Pipeline
- `2_engineer_features.py`: ~500 lines
- `3_create_labels.py`: ~600 lines
- `4_train_models.py`: ~400 lines
- **Total: ~1,500 lines**

### Grand Total: ~3,300 lines of Python code

---

## Workspace Status

### ✅ Clean & Organized
- Old files archived
- Clear structure
- Easy to navigate
- Well documented

### ✅ Production Ready
- Core files in place
- Models trained
- Tests passing
- Documentation complete

### ✅ Maintainable
- Modular design
- Clear naming
- Comprehensive docs
- Easy to extend

---

## Quick Navigation

### Want to...

**Run the system?**
→ `python scripts/test_enhanced_system.py`

**Understand the architecture?**
→ Read `TWO_STAGE_SYSTEM_COMPLETE.md`

**Get started quickly?**
→ Read `QUICK_START_ENHANCED.md`

**See what's new?**
→ Read `ENHANCED_SYSTEM_COMPLETE.md`

**Check system status?**
→ Read `SYSTEM_STATUS.md`

**Train new models?**
→ Run `scripts/4_train_models.py`

**Understand features?**
→ Read `documentation/FEATURE_EXTRACTION_LAYER.md`

---

**Status:** 🟢 Clean & Organized  
**Last Cleanup:** December 6, 2024
