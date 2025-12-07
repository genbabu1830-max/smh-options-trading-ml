#!/bin/bash

# Simple ML library installation script
# Uses pre-built wheels only, no compilation

echo "=== Installing ML Libraries (Simple Approach) ==="
echo ""

# Activate venv
source venv/bin/activate

echo "Step 1: Installing scipy (pre-built wheel)..."
pip install --only-binary=:all: scipy==1.11.4 || echo "scipy failed, trying older version..."
pip install --only-binary=:all: scipy==1.10.1 || echo "scipy still failing, will skip"

echo ""
echo "Step 2: Installing scikit-learn (pre-built wheel)..."
pip install --only-binary=:all: scikit-learn==1.3.2 || echo "scikit-learn failed, trying older..."
pip install --only-binary=:all: scikit-learn==1.2.2 || echo "scikit-learn still failing"

echo ""
echo "Step 3: Installing XGBoost..."
pip install xgboost==2.0.3 || pip install xgboost==1.7.6

echo ""
echo "Step 4: Installing LightGBM..."
pip install lightgbm==4.1.0 || pip install lightgbm==3.3.5

echo ""
echo "Step 5: Installing CatBoost..."
pip install catboost==1.2.2 || pip install catboost==1.1.1

echo ""
echo "Step 6: Installing remaining dependencies..."
pip install matplotlib seaborn joblib

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Verifying installations:"
python -c "import numpy; print(f'✓ NumPy {numpy.__version__}')" 2>/dev/null || echo "✗ NumPy failed"
python -c "import pandas; print(f'✓ Pandas {pandas.__version__}')" 2>/dev/null || echo "✗ Pandas failed"
python -c "import scipy; print(f'✓ SciPy {scipy.__version__}')" 2>/dev/null || echo "✗ SciPy failed"
python -c "import sklearn; print(f'✓ Scikit-learn {sklearn.__version__}')" 2>/dev/null || echo "✗ Scikit-learn failed"
python -c "import xgboost; print(f'✓ XGBoost {xgboost.__version__}')" 2>/dev/null || echo "✗ XGBoost failed"
python -c "import lightgbm; print(f'✓ LightGBM {lightgbm.__version__}')" 2>/dev/null || echo "✗ LightGBM failed"
python -c "import catboost; print(f'✓ CatBoost {catboost.__version__}')" 2>/dev/null || echo "✗ CatBoost failed"
python -c "import matplotlib; print(f'✓ Matplotlib {matplotlib.__version__}')" 2>/dev/null || echo "✗ Matplotlib failed"
python -c "import seaborn; print(f'✓ Seaborn {seaborn.__version__}')" 2>/dev/null || echo "✗ Seaborn failed"
python -c "import joblib; print(f'✓ Joblib {joblib.__version__}')" 2>/dev/null || echo "✗ Joblib failed"

echo ""
echo "Ready to train models!"
