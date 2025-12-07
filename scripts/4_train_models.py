"""
Model Training Script
Trains XGBoost, LightGBM, CatBoost, and Ensemble models
Compares performance and saves best model

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
# from xgboost import XGBClassifier  # XGBoost not available (compilation issues on Mac)
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

# Sklearn utilities
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, 
    classification_report, 
    confusion_matrix,
    top_k_accuracy_score
)
from sklearn.preprocessing import LabelEncoder

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


class StrategyModelTrainer:
    """
    Trains and evaluates multiple models for strategy prediction
    """
    
    def __init__(self, data_path='data/processed/smh_training_data.csv'):
        """Initialize trainer with data path"""
        self.data_path = data_path
        self.models = {}
        self.results = {}
        self.label_encoder = LabelEncoder()
        
        # Create directories
        Path('models').mkdir(exist_ok=True)
        Path('results').mkdir(exist_ok=True)
        
        print("=" * 80)
        print("STRATEGY MODEL TRAINER")
        print("=" * 80)
        print()
    
    def load_and_prepare_data(self):
        """Load training data and prepare features/labels"""
        print("Loading data...")
        df = pd.read_csv(self.data_path)
        
        # Identify feature columns (exclude target and metadata)
        exclude_cols = [
            'date', 'strategy',  # Target and date
            'long_strike', 'short_strike', 'dte', 'contracts',  # Parameters
            'expected_return', 'win_probability', 'max_profit', 'max_loss',  # Labels
            'risk_reward_ratio', 'avg_days_to_exit'  # Labels
        ]
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Separate features and target
        X = df[feature_cols].copy()
        y = df['strategy'].copy()
        
        # Encode strategy labels to integers
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Store for later use
        self.feature_names = feature_cols
        self.strategy_names = self.label_encoder.classes_
        self.n_classes = len(self.strategy_names)
        
        print(f"  Total samples: {len(df)}")
        print(f"  Features: {len(feature_cols)}")
        print(f"  Strategies: {self.n_classes}")
        print()
        
        print("Strategy distribution:")
        strategy_dist = y.value_counts()
        for strategy, count in strategy_dist.items():
            pct = count / len(y) * 100
            print(f"  {strategy:20s}: {count:3d} ({pct:5.1f}%)")
        print()
        
        # Handle missing values
        print("Handling missing values...")
        missing_counts = X.isnull().sum()
        cols_with_missing = missing_counts[missing_counts > 0]
        
        if len(cols_with_missing) > 0:
            print(f"  Found {len(cols_with_missing)} columns with missing values")
            for col, count in cols_with_missing.items():
                pct = count / len(X) * 100
                print(f"    {col}: {count} ({pct:.1f}%)")
            
            # Fill missing values with median (tree models handle this well)
            X = X.fillna(X.median())
            print("  Filled with median values")
        else:
            print("  No missing values found")
        print()
        
        # Train/test split (80/20, stratified)
        print("Splitting data (80% train, 20% test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, 
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
    
    def train_xgboost(self):
        """Train XGBoost model - SKIPPED (not available on this system)"""
        print("=" * 80)
        print("SKIPPING XGBOOST (not available)")
        print("=" * 80)
        print("XGBoost could not be installed due to compilation issues.")
        print("Using LightGBM and CatBoost instead.")
        print()
        return None, None
    
    def train_lightgbm(self):
        """Train LightGBM model"""
        print("=" * 80)
        print("TRAINING LIGHTGBM")
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
        print("TRAINING CATBOOST")
        print("=" * 80)
        print()
        
        model = CatBoostClassifier(
            iterations=100,
            depth=6,
            learning_rate=0.1,
            loss_function='MultiClass',
            random_seed=42,
            verbose=False,
            thread_count=-1
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
        """Create ensemble of LightGBM and CatBoost (XGBoost not available)"""
        print("=" * 80)
        print("CREATING ENSEMBLE")
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
        self._plot_confusion_matrix(cm, "Ensemble")
        
        # Store results
        results = {
            'accuracy': float(accuracy),
            'top3_accuracy': float(top3_accuracy),
            'test_samples': len(self.y_test),
            'confusion_matrix': cm.tolist()
        }
        
        self.results['ensemble'] = results
        
        # Save ensemble predictions function (without XGBoost)
        def ensemble_predict(X):
            lgb_proba = self.models['lightgbm'].predict_proba(X)
            cat_proba = self.models['catboost'].predict_proba(X)
            avg_proba = (lgb_proba + cat_proba) / 2  # Average of 2 models
            return np.argmax(avg_proba, axis=1), avg_proba
        
        self.ensemble_predict = ensemble_predict
        
        return ensemble_predict, results
    
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
        self._plot_confusion_matrix(cm, model_name)
        
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
            importance = model.feature_importances_
        elif hasattr(model, 'get_feature_importance'):
            importance = model.get_feature_importance()
        else:
            print(f"  {model_name} doesn't support feature importance")
            return
        
        # Create dataframe
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        # Save to CSV
        feature_importance.to_csv(
            f'results/{model_name.lower()}_feature_importance.csv', 
            index=False
        )
        
        # Plot top 20
        plt.figure(figsize=(10, 8))
        top20 = feature_importance.head(20)
        plt.barh(range(len(top20)), top20['importance'])
        plt.yticks(range(len(top20)), top20['feature'])
        plt.xlabel('Importance')
        plt.title(f'{model_name} - Top 20 Feature Importance')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(f'results/{model_name.lower()}_feature_importance.png', dpi=150)
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
        plt.title(f'{model_name} - Confusion Matrix')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(f'results/{model_name.lower()}_confusion_matrix.png', dpi=150)
        plt.close()
    
    def compare_models(self):
        """Compare all trained models"""
        print("=" * 80)
        print("MODEL COMPARISON")
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
        
        # Save comparison
        df_comparison.to_csv('results/model_comparison.csv', index=False)
        
        # Plot comparison
        self._plot_model_comparison()
        
        return df_comparison
    
    def _plot_model_comparison(self):
        """Plot model comparison"""
        models = list(self.results.keys())
        accuracies = [self.results[m]['accuracy'] * 100 for m in models]
        top3_accuracies = [self.results[m]['top3_accuracy'] * 100 for m in models]
        
        x = np.arange(len(models))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(x - width/2, accuracies, width, label='Accuracy', color='steelblue')
        ax.bar(x + width/2, top3_accuracies, width, label='Top-3 Accuracy', color='lightcoral')
        
        ax.set_xlabel('Model')
        ax.set_ylabel('Accuracy (%)')
        ax.set_title('Model Performance Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in models])
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, (acc, top3) in enumerate(zip(accuracies, top3_accuracies)):
            ax.text(i - width/2, acc + 1, f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)
            ax.text(i + width/2, top3 + 1, f'{top3:.1f}%', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig('results/model_comparison.png', dpi=150)
        plt.close()
    
    def save_models(self):
        """Save all trained models"""
        print("=" * 80)
        print("SAVING MODELS")
        print("=" * 80)
        print()
        
        # Save individual models
        for model_name, model in self.models.items():
            filepath = f'models/{model_name}_model.pkl'
            joblib.dump(model, filepath)
            print(f"  Saved {model_name} to {filepath}")
        
        # Save label encoder
        joblib.dump(self.label_encoder, 'models/label_encoder.pkl')
        print(f"  Saved label encoder to models/label_encoder.pkl")
        
        # Save feature names
        with open('models/feature_names.json', 'w') as f:
            json.dump(self.feature_names, f, indent=2)
        print(f"  Saved feature names to models/feature_names.json")
        
        # Save results
        with open('results/training_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"  Saved results to results/training_results.json")
        
        print()
        print("✓ All models saved successfully!")
        print()


def main():
    """Main training pipeline"""
    start_time = datetime.now()
    
    # Initialize trainer
    trainer = StrategyModelTrainer()
    
    # Load and prepare data
    trainer.load_and_prepare_data()
    
    # Train all models
    print("Training all models...")
    print()
    
    # trainer.train_xgboost()  # Skipped - not available
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
    print("TRAINING COMPLETE")
    print("=" * 80)
    print()
    print(f"Total training time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print()
    print("Next steps:")
    print("  1. Review results in results/ directory")
    print("  2. Check feature importance plots")
    print("  3. Analyze confusion matrices")
    print("  4. Compare model performance")
    print("  5. Select best model for production")
    print()
    print("Models saved in models/ directory")
    print("Results saved in results/ directory")
    print()


if __name__ == '__main__':
    main()
