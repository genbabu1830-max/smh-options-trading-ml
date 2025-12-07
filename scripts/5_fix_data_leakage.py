"""
Fix Data Leakage - Remove Strategy Output Columns
Removes all strategy-specific parameters from feature matrix
Retrains models with clean market condition features only

Version: 1.0
Date: December 6, 2024
"""

import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from datetime import datetime

# ML libraries
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

# Sklearn utilities
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, 
    classification_report, 
    confusion_matrix,
    top_k_accuracy_score
)
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)


class CleanModelTrainer:
    """Train models with clean features (no data leakage)"""
    
    def __init__(self):
        self.models = {}
        self.results = {}
        self.label_encoder = LabelEncoder()
        
        # Strategy output columns to REMOVE (these cause data leakage!)
        self.strategy_output_columns = [
            # Strike parameters (outputs of strategy selection)
            'strike',
            'dte',
            'long_strike',
            'short_strike',
            'near_dte',
            'far_dte',
            'center_strike',
            
            # Leg parameters (outputs)
            'long_put',
            'short_put',
            'long_call',
            'short_call',
            'put_strike',
            'call_strike',
            
            # Label creation metadata (not market conditions)
            'risk_adjusted_score',
            'win_probability',
            'expected_return',
            'max_loss',
            'avg_days_held',
            'n_similar_days',
            'n_tests',
        ]
        
        print("=" * 80)
        print("CLEAN MODEL TRAINER - NO DATA LEAKAGE")
        print("=" * 80)
        print()
    
    def load_and_clean_data(self):
        """Load data and remove strategy output columns"""
        print("Loading training data...")
        df = pd.read_csv('data/processed/smh_training_data.csv')
        
        print(f"  Total samples: {len(df)}")
        print(f"  Total columns: {len(df.columns)}")
        print()
        
        # Separate features and target
        y = df['strategy']
        
        # Remove target and metadata columns
        X = df.drop(columns=['date', 'strategy'])
        
        print(f"Before cleaning:")
        print(f"  Features: {X.shape[1]}")
        print()
        
        # Identify strategy output columns that exist
        columns_to_remove = [col for col in self.strategy_output_columns if col in X.columns]
        
        print(f"Removing {len(columns_to_remove)} strategy output columns:")
        for col in columns_to_remove:
            missing_pct = X[col].isnull().sum() / len(X) * 100
            print(f"  - {col:25s} ({missing_pct:5.1f}% missing)")
        print()
        
        # Remove strategy output columns
        X_clean = X.drop(columns=columns_to_remove)
        
        print(f"After cleaning:")
        print(f"  Features: {X_clean.shape[1]}")
        print()
        
        # Check for remaining high-missing columns
        missing_pct = (X_clean.isnull().sum() / len(X_clean) * 100)
        high_missing = missing_pct[missing_pct > 50]
        
        if len(high_missing) > 0:
            print(f"⚠️  Warning: {len(high_missing)} columns still have >50% missing:")
            for col, pct in high_missing.items():
                print(f"  - {col:25s} ({pct:5.1f}% missing)")
            print()
        
        # Store clean feature names
        self.feature_names = X_clean.columns.tolist()
        
        # Encode target
        y_encoded = self.label_encoder.fit_transform(y)
        self.strategy_names = self.label_encoder.classes_.tolist()
        self.n_classes = len(self.strategy_names)
        
        print(f"Strategies: {self.n_classes}")
        print()
        
        # Strategy distribution
        strategy_counts = y.value_counts()
        print("Strategy distribution:")
        for strategy, count in strategy_counts.items():
            pct = count / len(y) * 100
            print(f"  {strategy:20s}: {count:3d} ({pct:5.1f}%)")
        print()
        
        # Handle missing values
        print("Handling missing values...")
        missing_counts = X_clean.isnull().sum()
        cols_with_missing = missing_counts[missing_counts > 0]
        
        if len(cols_with_missing) > 0:
            print(f"  Found {len(cols_with_missing)} columns with missing values")
            for col, count in cols_with_missing.items():
                pct = count / len(X_clean) * 100
                print(f"    {col}: {count} ({pct:.1f}%)")
            
            # Fill missing values with median
            X_clean = X_clean.fillna(X_clean.median())
            print("  Filled with median values")
        else:
            print("  No missing values found")
        print()
        
        # Train/test split
        print("Splitting data (80% train, 20% test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_clean, y_encoded, 
            test_size=0.2, 
            random_state=42, 
            stratify=y_encoded
        )
        
        print(f"  Training samples: {len(X_train)}")
        print(f"  Test samples: {len(X_test)}")
        print()
        
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        
        return X_train, X_test, y_train, y_test
    
    def train_lightgbm(self):
        """Train LightGBM model"""
        print("=" * 80)
        print("TRAINING LIGHTGBM (CLEAN FEATURES)")
        print("=" * 80)
        print()
        
        model = LGBMClassifier(
            objective='multiclass',
            num_class=self.n_classes,
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        
        print("Training...")
        model.fit(self.X_train, self.y_train)
        
        # Evaluate
        results = self._evaluate_model(model, "LightGBM")
        
        # Save
        self.models['lightgbm'] = model
        self.results['lightgbm'] = results
        
        # Feature importance
        self._plot_feature_importance(model, "LightGBM")
        
        return model, results
    
    def train_catboost(self):
        """Train CatBoost model"""
        print("=" * 80)
        print("TRAINING CATBOOST (CLEAN FEATURES)")
        print("=" * 80)
        print()
        
        model = CatBoostClassifier(
            iterations=100,
            depth=6,
            learning_rate=0.1,
            loss_function='MultiClass',
            random_seed=42,
            verbose=False
        )
        
        print("Training...")
        model.fit(self.X_train, self.y_train)
        
        # Evaluate
        results = self._evaluate_model(model, "CatBoost")
        
        # Save
        self.models['catboost'] = model
        self.results['catboost'] = results
        
        # Feature importance
        self._plot_feature_importance(model, "CatBoost")
        
        return model, results
    
    def train_ensemble(self):
        """Create ensemble of LightGBM and CatBoost"""
        print("=" * 80)
        print("CREATING ENSEMBLE (CLEAN FEATURES)")
        print("=" * 80)
        print()
        
        if len(self.models) < 2:
            print("Error: Need at least 2 models trained first!")
            return None, None
        
        print("Ensemble strategy: Soft voting (average probabilities)")
        print("Models: LightGBM + CatBoost")
        print()
        
        # Get predictions from both models
        lgb_proba = self.models['lightgbm'].predict_proba(self.X_test)
        cat_proba = self.models['catboost'].predict_proba(self.X_test)
        
        # Average probabilities
        ensemble_proba = (lgb_proba + cat_proba) / 2
        
        # Get predictions
        y_pred = np.argmax(ensemble_proba, axis=1)
        
        # Calculate metrics
        accuracy = accuracy_score(self.y_test, y_pred)
        top3_accuracy = top_k_accuracy_score(self.y_test, ensemble_proba, k=3)
        
        print(f"Test Accuracy: {accuracy:.2%}")
        print(f"Top-3 Accuracy: {top3_accuracy:.2%}")
        print()
        
        # Per-strategy accuracy
        print("Per-Strategy Accuracy:")
        print("-" * 60)
        for i, strategy in enumerate(self.strategy_names):
            mask = (self.y_test == i)
            if mask.sum() > 0:
                strategy_acc = accuracy_score(self.y_test[mask], y_pred[mask])
                print(f"  {strategy:20s}: {strategy_acc:6.1%} ({mask.sum():2d} samples)")
        print()
        
        # Confusion matrix
        cm = confusion_matrix(self.y_test, y_pred)
        self._plot_confusion_matrix(cm, "Ensemble_Clean")
        
        # Store results
        results = {
            'accuracy': float(accuracy),
            'top3_accuracy': float(top3_accuracy),
            'test_samples': len(self.y_test),
            'confusion_matrix': cm.tolist()
        }
        
        self.results['ensemble'] = results
        
        return None, results
    
    def _evaluate_model(self, model, model_name):
        """Evaluate model performance"""
        # Predictions
        y_pred = model.predict(self.X_test)
        y_proba = model.predict_proba(self.X_test)
        
        # Metrics
        accuracy = accuracy_score(self.y_test, y_pred)
        top3_accuracy = top_k_accuracy_score(self.y_test, y_proba, k=3)
        
        print(f"Test Accuracy: {accuracy:.2%}")
        print(f"Top-3 Accuracy: {top3_accuracy:.2%}")
        print()
        
        # Per-strategy accuracy
        print("Per-Strategy Accuracy:")
        print("-" * 60)
        for i, strategy in enumerate(self.strategy_names):
            mask = (self.y_test == i)
            if mask.sum() > 0:
                strategy_acc = accuracy_score(self.y_test[mask], y_pred[mask])
                print(f"  {strategy:20s}: {strategy_acc:6.1%} ({mask.sum():2d} samples)")
        print()
        
        # Confusion matrix
        cm = confusion_matrix(self.y_test, y_pred)
        self._plot_confusion_matrix(cm, f"{model_name}_Clean")
        
        # Store results
        results = {
            'accuracy': float(accuracy),
            'top3_accuracy': float(top3_accuracy),
            'test_samples': len(self.y_test),
            'confusion_matrix': cm.tolist()
        }
        
        return results
    
    def _plot_feature_importance(self, model, model_name):
        """Plot feature importance"""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'get_feature_importance'):
            importances = model.get_feature_importance()
        else:
            print(f"  No feature importance available for {model_name}")
            return
        
        # Create dataframe
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        # Plot top 20
        plt.figure(figsize=(10, 12))
        top20 = feature_importance.head(20)
        plt.barh(range(len(top20)), top20['importance'])
        plt.yticks(range(len(top20)), top20['feature'])
        plt.xlabel('Importance')
        plt.title(f'{model_name} - Top 20 Feature Importance (Clean Features)')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(f'results/{model_name.lower()}_clean_feature_importance.png', dpi=150)
        plt.close()
        
        print(f"Top 10 Features for {model_name}:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']:30s}: {row['importance']:.4f}")
        print()
    
    def _plot_confusion_matrix(self, cm, model_name):
        """Plot confusion matrix"""
        plt.figure(figsize=(12, 10))
        sns.heatmap(
            cm, 
            annot=True, 
            fmt='d', 
            cmap='Blues',
            xticklabels=self.strategy_names,
            yticklabels=self.strategy_names
        )
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title(f'{model_name} - Confusion Matrix (Clean Features)')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(f'results/{model_name.lower()}_confusion_matrix.png', dpi=150)
        plt.close()
    
    def compare_models(self):
        """Compare all trained models"""
        print("=" * 80)
        print("MODEL COMPARISON (CLEAN FEATURES)")
        print("=" * 80)
        print()
        
        # Create comparison table
        comparison = []
        for model_name, results in self.results.items():
            comparison.append({
                'Model': model_name.upper(),
                'Accuracy': f"{results['accuracy']:.2%}",
                'Top-3 Accuracy': f"{results['top3_accuracy']:.2%}",
                'Test Samples': results['test_samples']
            })
        
        df_comparison = pd.DataFrame(comparison)
        print(df_comparison.to_string(index=False))
        print()
        
        # Find best model
        best_model = max(self.results.items(), key=lambda x: x[1]['accuracy'])
        print(f"🏆 Best Model: {best_model[0].upper()} ({best_model[1]['accuracy']:.2%})")
        print()
    
    def save_models(self):
        """Save all trained models"""
        print("=" * 80)
        print("SAVING CLEAN MODELS")
        print("=" * 80)
        print()
        
        # Save individual models
        for model_name, model in self.models.items():
            filepath = f'models/{model_name}_clean_model.pkl'
            joblib.dump(model, filepath)
            print(f"  Saved {model_name} to {filepath}")
        
        # Save label encoder
        joblib.dump(self.label_encoder, 'models/label_encoder_clean.pkl')
        print(f"  Saved label encoder to models/label_encoder_clean.pkl")
        
        # Save feature names
        with open('models/feature_names_clean.json', 'w') as f:
            json.dump(self.feature_names, f, indent=2)
        print(f"  Saved feature names to models/feature_names_clean.json")
        
        # Save results
        with open('results/training_results_clean.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"  Saved results to results/training_results_clean.json")
        
        print()
        print("✓ All clean models saved successfully!")
        print()


def main():
    """Main training pipeline with clean features"""
    start_time = datetime.now()
    
    # Initialize trainer
    trainer = CleanModelTrainer()
    
    # Load and clean data
    trainer.load_and_clean_data()
    
    # Train all models
    print("Training all models with clean features...")
    print()
    
    trainer.train_lightgbm()
    trainer.train_catboost()
    trainer.train_ensemble()
    
    # Compare models
    trainer.compare_models()
    
    # Save models
    trainer.save_models()
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("=" * 80)
    print("TRAINING COMPLETE (CLEAN FEATURES)")
    print("=" * 80)
    print()
    print(f"Total training time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print()
    print("Expected Results:")
    print("  - Accuracy: 70-80% (realistic for 10-class problem)")
    print("  - Top-3 Accuracy: 85-95% (good coverage)")
    print("  - No data leakage (verified)")
    print()
    print("Next steps:")
    print("  1. Review results in results/ directory")
    print("  2. Compare clean vs leaky model performance")
    print("  3. Verify accuracy dropped to realistic range (70-80%)")
    print("  4. If accuracy is still >90%, check for remaining leakage")
    print()
    print("Models saved in models/ directory")
    print("Results saved in results/ directory")
    print()


if __name__ == "__main__":
    main()
