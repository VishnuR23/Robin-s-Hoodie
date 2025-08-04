import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from data_bridge.redis_data_client import RedisDataClient
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

class RSIMLStrategy:
    """
    Advanced RSI Strategy with Machine Learning
    - Uses data from C++ engine via Redis
    - Combines RSI with ML predictions
    - Includes backtesting and performance analysis
    """
    
    def __init__(self, rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.redis_client = RedisDataClient()
        self.ml_model = None
        self.is_trained = False
        
        print("🤖 RSI ML Strategy Initialized")
        print(f"   RSI Period: {rsi_period}")
        print(f"   Oversold Threshold: {oversold}")
        print(f"   Overbought Threshold: {overbought}")
        print(f"   Redis Connection: {'✅' if self.redis_client.is_connected() else '❌'}")
    
    def get_enhanced_data(self, symbol: str, period: str = "6mo") -> pd.DataFrame:
        """Get data from multiple sources and enhance it"""
        print(f"📊 Getting enhanced data for {symbol}...")
        
        # Try to get data from Redis first (from C++ engine)
        redis_data = self.redis_client.get_current_stock_data(symbol)
        
        # Get historical data from yfinance for ML training
        ticker = yf.Ticker(symbol)
        hist_data = ticker.history(period=period)
        
        if hist_data.empty:
            print(f"❌ No historical data for {symbol}")
            return pd.DataFrame()
        
        # Clean and prepare data
        df = hist_data.reset_index()
        df.columns = [col.lower() for col in df.columns]
        
        # Add current data from Redis if available
        if redis_data:
            current_row = {
                'date': pd.Timestamp.now(),
                'open': redis_data.get('current_price', df['close'].iloc[-1]),
                'high': redis_data.get('day_high', df['high'].iloc[-1]),
                'low': redis_data.get('day_low', df['low'].iloc[-1]),
                'close': redis_data['current_price'],
                'volume': redis_data.get('volume', df['volume'].iloc[-1])
            }
            df = pd.concat([df, pd.DataFrame([current_row])], ignore_index=True)
            print(f"📡 Added current data from C++ engine: ${redis_data['current_price']:.2f}")
        
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators for ML"""
        print("🔧 Calculating technical indicators...")
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # Moving Averages
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        rolling_mean = df['close'].rolling(window=20).mean()
        rolling_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = rolling_mean + (rolling_std * 2)
        df['bb_lower'] = rolling_mean - (rolling_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Price momentum and volatility
        df['price_change'] = df['close'].pct_change()
        df['price_change_1d'] = df['close'].pct_change(1)
        df['price_change_5d'] = df['close'].pct_change(5)
        df['volatility'] = df['close'].rolling(window=10).std()
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Relative position indicators
        df['price_vs_sma20'] = (df['close'] - df['sma_20']) / df['sma_20'] * 100
        df['price_vs_sma50'] = (df['close'] - df['sma_50']) / df['sma_50'] * 100
        
        # Support/Resistance levels
        df['high_20'] = df['high'].rolling(window=20).max()
        df['low_20'] = df['low'].rolling(window=20).min()
        df['position_in_range'] = (df['close'] - df['low_20']) / (df['high_20'] - df['low_20'])
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def create_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for machine learning model"""
        print("🧠 Creating ML features...")
        
        # Calculate technical indicators
        df = self.calculate_technical_indicators(df)
        
        # Create target variable (future price movement)
        df['future_return'] = df['close'].shift(-1) / df['close'] - 1
        df['target'] = np.where(df['future_return'] > 0.005, 1,  # Strong up
                               np.where(df['future_return'] < -0.005, -1, 0))  # Strong down, else hold
        
        # Select features for ML model
        feature_columns = [
            'rsi', 'macd', 'macd_histogram', 'bb_position',
            'price_vs_sma20', 'price_vs_sma50', 'volatility',
            'volume_ratio', 'position_in_range', 'price_change_5d'
        ]
        
        # Remove rows with NaN values
        df_clean = df[feature_columns + ['target']].dropna()
        
        print(f"✅ Created {len(df_clean)} samples with {len(feature_columns)} features")
        return df_clean, feature_columns
    
    def train_ml_model(self, symbol: str) -> bool:
        """Train machine learning model on historical data"""
        print(f"🧠 Training ML model for {symbol}...")
        
        # Get historical data
        df = self.get_enhanced_data(symbol, period="1y")
        if df.empty:
            return False
        
        # Create ML features
        ml_data, feature_columns = self.create_ml_features(df)
        if len(ml_data) < 50:
            print("❌ Insufficient data for ML training")
            return False
        
        # Prepare data for training
        X = ml_data[feature_columns]
        y = ml_data['target']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Random Forest model
        self.ml_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.ml_model.fit(X_train, y_train)
        self.feature_columns = feature_columns
        
        # Evaluate model
        y_pred = self.ml_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ ML Model trained with {accuracy:.2%} accuracy")
        print("📊 Feature Importance:")
        
        feature_importance = sorted(
            zip(feature_columns, self.ml_model.feature_importances_),
            key=lambda x: x[1], reverse=True
        )
        
        for feature, importance in feature_importance[:5]:
            print(f"   {feature}: {importance:.3f}")
        
        self.is_trained = True
        return True
    
    def generate_signal(self, symbol: str) -> Dict:
        """Generate trading signal combining RSI and ML"""
        print(f"\n🎯 Generating signal for {symbol}...")
        
        # Get current data
        df = self.get_enhanced_data(symbol, period="3mo")
        if df.empty:
            return {"error": "No data available"}
        
        # Calculate indicators
        df = self.calculate_technical_indicators(df)
        
        # Get latest values
        latest = df.iloc[-1]
        current_price = latest['close']
        rsi = latest['rsi']
        
        print(f"💰 Current Price: ${current_price:.2f}")
        print(f"📊 RSI: {rsi:.1f}")
        
        # Traditional RSI signal
        if rsi <= self.oversold:
            rsi_signal = "BUY"
            rsi_reason = f"RSI ({rsi:.1f}) oversold"
            rsi_confidence = min(90, (self.oversold - rsi) * 2 + 70)
        elif rsi >= self.overbought:
            rsi_signal = "SELL"
            rsi_reason = f"RSI ({rsi:.1f}) overbought"
            rsi_confidence = min(90, (rsi - self.overbought) * 2 + 70)
        else:
            rsi_signal = "HOLD"
            rsi_reason = f"RSI ({rsi:.1f}) neutral"
            rsi_confidence = 50
        
        # ML prediction if model is trained
        ml_signal = "HOLD"
        ml_confidence = 50
        ml_reason = "No ML model"
        
        if self.is_trained and self.ml_model:
            try:
                # Prepare features for ML prediction
                ml_features = latest[self.feature_columns].values.reshape(1, -1)
                
                # Get ML prediction
                ml_pred = self.ml_model.predict(ml_features)[0]
                ml_proba = self.ml_model.predict_proba(ml_features)[0]
                
                if ml_pred == 1:
                    ml_signal = "BUY"
                    ml_confidence = ml_proba[np.argmax(ml_proba)] * 100
                    ml_reason = "ML predicts price increase"
                elif ml_pred == -1:
                    ml_signal = "SELL"  
                    ml_confidence = ml_proba[np.argmax(ml_proba)] * 100
                    ml_reason = "ML predicts price decrease"
                else:
                    ml_signal = "HOLD"
                    ml_confidence = ml_proba[np.argmax(ml_proba)] * 100
                    ml_reason = "ML predicts sideways movement"
                
                print(f"🧠 ML Prediction: {ml_signal} ({ml_confidence:.1f}%)")
                
            except Exception as e:
                print(f"❌ ML prediction error: {e}")
        
        # Combine RSI and ML signals
        final_signal, final_confidence, final_reason = self._combine_signals(
            rsi_signal, rsi_confidence, ml_signal, ml_confidence
        )
        
        # Store prediction back to Redis
        if self.redis_client.is_connected():
            self.redis_client.store_ml_prediction(
                symbol, final_signal, final_confidence, "RSI_ML_Strategy"
            )
        
        result = {
            "symbol": symbol,
            "signal": final_signal,
            "confidence": final_confidence,
            "reason": final_reason,
            "rsi": rsi,
            "current_price": current_price,
            "rsi_signal": rsi_signal,
            "ml_signal": ml_signal,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "rsi": {"signal": rsi_signal, "confidence": rsi_confidence, "reason": rsi_reason},
                "ml": {"signal": ml_signal, "confidence": ml_confidence, "reason": ml_reason}
            }
        }
        
        print(f"🎯 Final Signal: {final_signal} (Confidence: {final_confidence:.1f}%)")
        print(f"💡 Reason: {final_reason}")
        
        return result
    
    def _combine_signals(self, rsi_signal: str, rsi_conf: float, 
                        ml_signal: str, ml_conf: float) -> Tuple[str, float, str]:
        """Combine RSI and ML signals intelligently"""
        
        # If both agree, high confidence
        if rsi_signal == ml_signal:
            combined_conf = min(95, (rsi_conf + ml_conf) / 2 + 10)
            reason = f"RSI and ML both suggest {rsi_signal}"
            return rsi_signal, combined_conf, reason
        
        # If they disagree, use the one with higher confidence
        if rsi_conf > ml_conf:
            reason = f"RSI ({rsi_signal}) overrides ML ({ml_signal})"
            return rsi_signal, rsi_conf * 0.8, reason
        else:
            reason = f"ML ({ml_signal}) overrides RSI ({rsi_signal})"
            return ml_signal, ml_conf * 0.8, reason
    
    def run_strategy(self, symbols: List[str], train_models: bool = True) -> List[Dict]:
        """Run the complete strategy on multiple symbols"""
        print("🚀 STARTING RSI ML TRADING STRATEGY")
        print("=" * 60)
        print(f"📊 Analyzing {len(symbols)} symbols")
        print(f"🧠 ML Training: {'Enabled' if train_models else 'Disabled'}")
        print()
        
        results = []
        
        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] Processing {symbol}...")
            
            try:
                # Train ML model if requested
                if train_models:
                    print(f"🧠 Training ML model for {symbol}...")
                    training_success = self.train_ml_model(symbol)
                    if training_success:
                        print(f"✅ ML model trained for {symbol}")
                    else:
                        print(f"⚠️ ML training failed for {symbol}, using RSI only")
                
                # Generate signal
                signal_result = self.generate_signal(symbol)
                results.append(signal_result)
                
                print(f"✅ {symbol} analysis complete")
                print("-" * 40)
                
                # Brief pause between symbols
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                results.append({
                    "symbol": symbol,
                    "signal": "ERROR",
                    "reason": str(e),
                    "error": True
                })
        
        return results
    
    def display_portfolio_summary(self, results: List[Dict]):
        """Display comprehensive portfolio analysis"""
        print("\n" + "=" * 60)
        print("📈 RSI ML STRATEGY PORTFOLIO SUMMARY")
        print("=" * 60)
        
        # Filter successful results
        valid_results = [r for r in results if not r.get('error', False)]
        
        if not valid_results:
            print("❌ No valid results to display")
            return
        
        # Categorize signals
        buy_signals = [r for r in valid_results if r['signal'] == 'BUY']
        sell_signals = [r for r in valid_results if r['signal'] == 'SELL']
        hold_signals = [r for r in valid_results if r['signal'] == 'HOLD']
        
        # Display by category
        print(f"\n🟢 BUY SIGNALS ({len(buy_signals)}):")
        for signal in sorted(buy_signals, key=lambda x: x['confidence'], reverse=True):
            print(f"   {signal['symbol']}: {signal['confidence']:.1f}% - {signal['reason']}")
            print(f"      RSI: {signal.get('rsi', 'N/A'):.1f} | Price: ${signal.get('current_price', 0):.2f}")
        
        print(f"\n🔴 SELL SIGNALS ({len(sell_signals)}):")
        for signal in sorted(sell_signals, key=lambda x: x['confidence'], reverse=True):
            print(f"   {signal['symbol']}: {signal['confidence']:.1f}% - {signal['reason']}")
            print(f"      RSI: {signal.get('rsi', 'N/A'):.1f} | Price: ${signal.get('current_price', 0):.2f}")
        
        print(f"\n🟡 HOLD SIGNALS ({len(hold_signals)}):")
        for signal in hold_signals:
            print(f"   {signal['symbol']}: RSI {signal.get('rsi', 'N/A'):.1f}")
        
        # Summary statistics
        avg_confidence = np.mean([r['confidence'] for r in valid_results])
        high_confidence_signals = [r for r in valid_results if r['confidence'] > 70]
        
        print(f"\n📊 PORTFOLIO STATISTICS:")
        print(f"   Average Confidence: {avg_confidence:.1f}%")
        print(f"   High Confidence Signals (>70%): {len(high_confidence_signals)}")
        print(f"   ML Models Trained: {len([r for r in valid_results if 'ml_signal' in r])}")
        
        # Top recommendations
        print(f"\n⭐ TOP RECOMMENDATIONS:")
        top_signals = sorted(valid_results, key=lambda x: x['confidence'], reverse=True)[:3]
        for i, signal in enumerate(top_signals, 1):
            print(f"   {i}. {signal['symbol']}: {signal['signal']} ({signal['confidence']:.1f}%)")
        
        print("=" * 60)


def main():
    """Main function to run the RSI ML strategy"""
    print("🤖 RSI MACHINE LEARNING TRADING STRATEGY")
    print("=" * 50)
    
    # Initialize strategy
    strategy = RSIMLStrategy(rsi_period=14, oversold=30, overbought=70)
    
    if not strategy.redis_client.is_connected():
        print("❌ Redis not connected. Make sure to:")
        print("   1. Start Redis: docker-compose up -d redis")
        print("   2. Run C++ engine to populate data")
        return
    
    # Define watchlist
    watchlist = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMZN"]
    
    print(f"📊 Watchlist: {', '.join(watchlist)}")
    print()
    
    # Run strategy with ML training
    results = strategy.run_strategy(watchlist, train_models=True)
    
    # Display results
    strategy.display_portfolio_summary(results)
    
    # Save results
    import json
    with open("rsi_ml_signals.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to rsi_ml_signals.json")
    print("🎯 Strategy execution completed!")


if __name__ == "__main__":
    main()