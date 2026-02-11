import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import logging
from datetime import datetime

class StrikeIQModel:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.model = None

    def train(self, df: pd.DataFrame, symbol: str):
        """
        Train a binary classifier for bullish movement
        """
        if df.empty or len(df) < 50:
            logging.warning(f"Not enough data to train for {symbol}")
            return False
            
        # Define features (exclude labels and non-numeric)
        drop_cols = ['id', 'symbol', 'timestamp', 'label_move_30m', 'label_bullish', 'market_status', 'regime']
        X = df.drop(columns=[c for c in drop_cols if c in df.columns], errors='ignore')
        y = df['label_bullish']
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        # Train XGBoost
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='binary:logistic'
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        logging.info(f"Model for {symbol} trained. Accuracy: {acc:.4f}")
        
        # Save model
        model_path = os.path.join(self.model_dir, f"{symbol}_bullish_v1.joblib")
        joblib.dump(self.model, model_path)
        
        # Save feature list for inference
        feature_path = os.path.join(self.model_dir, f"{symbol}_features.joblib")
        joblib.dump(list(X.columns), feature_path)
        
        return True

    def predict_probability(self, feature_dict: Dict[str, Any], symbol: str):
        """
        Predict probability for a single feature vector
        """
        model_path = os.path.join(self.model_dir, f"{symbol}_bullish_v1.joblib")
        feature_path = os.path.join(self.model_dir, f"{symbol}_features.joblib")
        
        if not os.path.exists(model_path):
            return 0.5 # Neutral
            
        model = joblib.load(model_path)
        features = joblib.load(feature_path)
        
        # Align features
        input_data = []
        for f in features:
            input_data.append(feature_dict.get(f, 0))
            
        X = pd.DataFrame([input_data], columns=features)
        probs = model.predict_proba(X)
        
        return float(probs[0][1]) # Return bullish probability
