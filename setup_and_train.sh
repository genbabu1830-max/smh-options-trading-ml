#!/bin/bash
# Setup and Train ML Models
# This script creates environment and trains all models

set -e  # Exit on error

echo "=========================================="
echo "ML MODEL TRAINING SETUP"
echo "=========================================="
echo ""

# Step 1: Create conda environment
echo "[1/4] Creating conda environment 'options-ml'..."
conda create -n options-ml python=3.10 -y > /dev/null 2>&1 || echo "Environment already exists"
echo "✓ Environment created"
echo ""

# Step 2: Install packages
echo "[2/4] Installing ML libraries (this may take 5-10 minutes)..."
echo "  Installing: xgboost, lightgbm, catboost, scikit-learn, pandas, numpy, matplotlib, seaborn, joblib"
echo ""

# Activate environment and install
eval "$(conda shell.bash hook)"
conda activate options-ml

# Install in smaller batches for faster resolution
echo "  → Installing core packages..."
conda install -c conda-forge pandas numpy -y -q

echo "  → Installing scikit-learn..."
conda install -c conda-forge scikit-learn -y -q

echo "  → Installing visualization..."
conda install -c conda-forge matplotlib seaborn -y -q

echo "  → Installing XGBoost..."
conda install -c conda-forge xgboost -y -q

echo "  → Installing LightGBM..."
conda install -c conda-forge lightgbm -y -q

echo "  → Installing CatBoost..."
conda install -c conda-forge catboost -y -q

echo "  → Installing joblib..."
conda install -c conda-forge joblib -y -q

echo "✓ All libraries installed"
echo ""

# Step 3: Verify installation
echo "[3/4] Verifying installation..."
python -c "
import xgboost
import lightgbm
import catboost
import sklearn
import pandas
import numpy
import matplotlib
import seaborn
import joblib
print('✓ XGBoost version:', xgboost.__version__)
print('✓ LightGBM version:', lightgbm.__version__)
print('✓ CatBoost version:', catboost.__version__)
print('✓ Scikit-learn version:', sklearn.__version__)
print('✓ All libraries verified!')
"
echo ""

# Step 4: Train models
echo "[4/4] Training models..."
echo "  This will take 6-10 minutes"
echo "  Progress will be shown below:"
echo ""
python scripts/4_train_models.py

echo ""
echo "=========================================="
echo "SETUP AND TRAINING COMPLETE!"
echo "=========================================="
echo ""
echo "Results saved in:"
echo "  - models/     (trained models)"
echo "  - results/    (metrics, plots, comparisons)"
echo ""
echo "To use this environment in future:"
echo "  conda activate options-ml"
echo ""
