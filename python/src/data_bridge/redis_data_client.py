import redis
import json
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class RedisDataClient:
    """
    Python client that reads market data from Redis
    (stored by our C++ engine) instead of duplicating API calls
    """
    
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.connected = True
            print(f"✅ Connected to Redis at {host}:{port}")
            print("🔗 Ready to read data from C++ engine")
        except redis.ConnectionError as e:
            print(f"❌ Failed to connect to Redis: {e}")
            print("💡 Make sure Redis is running: docker-compose up -d redis")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if Redis connection is active"""
        return self.connected
    
    def get_current_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get the latest stock data for a symbol (from C++ engine)"""
        if not self.connected:
            return None
        
        try:
            key = f"stock:current:{symbol}"
            data = self.redis_client.get(key)
            
            if data:
                stock_data = json.loads(data)
                print(f"📊 Retrieved {symbol} data from C++ engine: ${stock_data['current_price']:.2f}")
                return stock_data
            else:
                print(f"❌ No data found for {symbol} in Redis")
                return None
                
        except Exception as e:
            print(f"❌ Error reading {symbol} from Redis: {e}")
            return None
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get current data for multiple stocks from Redis"""
        print(f"📊 Reading data for {len(symbols)} stocks from Redis...")
        
        results = {}
        for symbol in symbols:
            data = self.get_current_stock_data(symbol)
            if data:
                results[symbol] = data
        
        print(f"✅ Retrieved data for {len(results)} stocks from C++ engine")
        return results
    
    def get_historical_data(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """Get historical data from Redis (stored by C++ engine)"""
        if not self.connected:
            return pd.DataFrame()
        
        try:
            key = f"stock:history:{symbol}"
            # Get historical data (stored as list in Redis)
            historical_data = self.redis_client.lrange(key, 0, limit-1)
            
            if not historical_data:
                print(f"❌ No historical data for {symbol}")
                return pd.DataFrame()
            
            # Convert JSON strings to DataFrame
            records = []
            for data_str in historical_data:
                record = json.loads(data_str)
                records.append(record)
            
            df = pd.DataFrame(records)
            
            # Convert timestamp to datetime
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('datetime').reset_index(drop=True)
            
            print(f"📈 Retrieved {len(df)} historical records for {symbol}")
            return df
            
        except Exception as e:
            print(f"❌ Error reading historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_latest_trading_signal(self, symbol: str) -> Optional[Dict]:
        """Get the latest trading signal for a symbol (from C++ engine)"""
        if not self.connected:
            return None
        
        try:
            key = f"signal:latest:{symbol}"
            signal_data = self.redis_client.get(key)
            
            if signal_data:
                signal = json.loads(signal_data)
                print(f"🤖 Latest signal for {symbol}: {signal['signal']} ({signal['confidence']:.1f}%)")
                return signal
            else:
                print(f"❌ No trading signal found for {symbol}")
                return None
                
        except Exception as e:
            print(f"❌ Error reading signal for {symbol}: {e}")
            return None
    
    def get_all_available_symbols(self) -> List[str]:
        """Get list of all symbols that have data in Redis"""
        if not self.connected:
            return []
        
        try:
            # Find all stock data keys
            keys = self.redis_client.keys("stock:current:*")
            symbols = [key.split(":")[-1] for key in keys]
            
            print(f"📊 Found data for {len(symbols)} symbols: {', '.join(symbols)}")
            return symbols
            
        except Exception as e:
            print(f"❌ Error getting available symbols: {e}")
            return []
    
    def wait_for_new_data(self, timeout: int = 30) -> Optional[Dict]:
        """Wait for new market data updates from C++ engine"""
        if not self.connected:
            return None
        
        try:
            print(f"⏳ Waiting for new market data from C++ engine (timeout: {timeout}s)...")
            
            # Subscribe to market updates channel
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe('market_updates')
            
            # Wait for new message
            message = pubsub.get_message(timeout=timeout)
            
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                print(f"📡 Received real-time update: {data['symbol']} = ${data['current_price']:.2f}")
                pubsub.unsubscribe('market_updates')
                return data
            else:
                print("⏰ No new data received within timeout")
                pubsub.unsubscribe('market_updates')
                return None
                
        except Exception as e:
            print(f"❌ Error waiting for new data: {e}")
            return None
    
    def create_ml_dataset(self, symbol: str) -> pd.DataFrame:
        """Create ML-ready dataset from Redis historical data"""
        print(f"🤖 Creating ML dataset for {symbol} from C++ engine data...")
        
        # Get historical data from Redis
        df = self.get_historical_data(symbol, limit=200)
        
        if df.empty:
            return df
        
        # Calculate technical indicators for ML
        df = self._add_technical_indicators(df)
        
        # Remove NaN values
        df = df.dropna()
        
        print(f"✅ ML dataset ready: {len(df)} samples with {len(df.columns)} features")
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataset"""
        # Ensure we have the price column
        if 'current_price' not in df.columns:
            print("❌ No price data found")
            return df
        
        # Rename for consistency
        df['close'] = df['current_price']
        
        # Moving averages
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        
        # RSI calculation
        df['rsi'] = self._calculate_rsi(df['close'])
        
        # Price momentum
        df['momentum_1'] = df['close'].pct_change(1)
        df['momentum_5'] = df['close'].pct_change(5)
        
        # Volatility
        df['volatility'] = df['close'].rolling(window=10).std()
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def store_ml_prediction(self, symbol: str, prediction: str, confidence: float, model_name: str):
        """Store ML prediction back to Redis for C++ engine to use"""
        if not self.connected:
            return False
        
        try:
            prediction_data = {
                "symbol": symbol,
                "prediction": prediction,
                "confidence": confidence,
                "model_name": model_name,
                "timestamp": time.time(),
                "source": "python_ml"
            }
            
            key = f"ml_prediction:{symbol}"
            self.redis_client.set(key, json.dumps(prediction_data))
            
            # Also publish to predictions channel
            self.redis_client.publish("ml_predictions", json.dumps(prediction_data))
            
            print(f"🧠 Stored ML prediction: {symbol} -> {prediction} ({confidence:.1f}%)")
            return True
            
        except Exception as e:
            print(f"❌ Error storing ML prediction: {e}")
            return False


def test_redis_bridge():
    """Test the Redis data bridge"""
    print("🧪 TESTING REDIS DATA BRIDGE")
    print("=" * 50)
    
    # Initialize Redis client
    client = RedisDataClient()
    
    if not client.is_connected():
        print("❌ Redis not connected. Start with: docker-compose up -d redis")
        return
    
    # Test 1: Get available symbols
    print("\n📊 TEST 1: Available Symbols")
    symbols = client.get_all_available_symbols()
    
    if not symbols:
        print("❌ No data found. Run the C++ engine first to populate Redis!")
        return
    
    # Test 2: Get current data
    print("\n📊 TEST 2: Current Stock Data")
    for symbol in symbols[:3]:  # Test first 3 symbols
        data = client.get_current_stock_data(symbol)
        if data:
            print(f"  {symbol}: ${data['current_price']:.2f} ({data['change_percent']:+.1f}%)")
    
    # Test 3: Get trading signals
    print("\n📊 TEST 3: Trading Signals")
    for symbol in symbols[:3]:
        signal = client.get_latest_trading_signal(symbol)
        if signal:
            print(f"  {symbol}: {signal['signal']} - {signal['reason']}")
    
    # Test 4: Historical data
    print("\n📊 TEST 4: Historical Data")
    if symbols:
        hist_data = client.get_historical_data(symbols[0])
        if not hist_data.empty:
            print(f"  {symbols[0]}: {len(hist_data)} historical records")
    
    # Test 5: ML Dataset
    print("\n📊 TEST 5: ML Dataset Creation")
    if symbols:
        ml_data = client.create_ml_dataset(symbols[0])
        if not ml_data.empty:
            print(f"  ML Dataset: {len(ml_data)} samples, {len(ml_data.columns)} features")
            if 'rsi' in ml_data.columns:
                print(f"  Latest RSI: {ml_data['rsi'].iloc[-1]:.1f}")
    
    print("\n✅ Redis bridge tests completed!")
    print("🔗 Python can now read data from C++ engine!")


if __name__ == "__main__":
    test_redis_bridge()