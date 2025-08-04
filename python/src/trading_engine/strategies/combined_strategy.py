import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from trading_engine.strategies.rsi_ml_strategy import RSIMLStrategy
from sentiment.news_sentiment_analyzer import NewsSentimentAnalyzer
from data_bridge.redis_data_client import RedisDataClient
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple

class CombinedTradingStrategy:
    """
    Strategy Combining:
    1. Technical Analysis (RSI + ML)
    2. Sentiment Analysis (News + Social Media)
    3. Market Data from C++ Engine
    """
    
    def __init__(self):
        self.rsi_strategy = RSIMLStrategy()
        self.sentiment_analyzer = NewsSentimentAnalyzer()
        self.redis_client = RedisDataClient()
        
        print("🚀 COMBINED AI TRADING STRATEGY INITIALIZED")
        print("=" * 50)
        print("🔧 Components loaded:")
        print("   ✅ RSI + ML Strategy")
        print("   ✅ News Sentiment Analyzer") 
        print("   ✅ Redis Data Bridge")
        print(f"   🔗 Redis Connection: {'✅' if self.redis_client.is_connected() else '❌'}")
    
    def generate_ultimate_signal(self, symbol: str) -> Dict:
        """Generate the ultimate trading signal combining all AI methods"""
        print(f"\n🎯 ULTIMATE AI ANALYSIS FOR {symbol}")
        print("=" * 60)
        
        # 1. Get RSI + ML signal
        print("📊 [1/3] Getting Technical + ML Analysis...")
        rsi_ml_result = self.rsi_strategy.generate_signal(symbol)
        
        # 2. Get sentiment analysis
        print("📰 [2/3] Getting News Sentiment Analysis...")
        sentiment_signal = self.sentiment_analyzer.get_sentiment_trading_signal(symbol)
        
        # 3. Get current market data from C++ engine
        print("💾 [3/3] Getting Real-time Market Data...")
        market_data = self.redis_client.get_current_stock_data(symbol)
        
        # Combine all signals intelligently
        final_signal = self._combine_all_signals(rsi_ml_result, sentiment_signal, market_data)
        
        # Store the ultimate signal in Redis
        if self.redis_client.is_connected():
            self.redis_client.redis_client.set(
                f"ultimate_signal:{symbol}",
                json.dumps(final_signal, default=str),
                ex=1800  # 30 minutes
            )
        
        return final_signal
    
    def _combine_all_signals(self, rsi_ml: Dict, sentiment: Dict, market_data: Dict) -> Dict:
        """Intelligently combine RSI/ML, sentiment, and market data"""
        
        symbol = rsi_ml.get('symbol', 'UNKNOWN')
        
        # Extract signal components
        rsi_signal = rsi_ml.get('signal', 'HOLD')
        rsi_confidence = rsi_ml.get('confidence', 50)
        
        sentiment_signal = self._normalize_sentiment_signal(sentiment.get('sentiment_signal', 'HOLD'))
        sentiment_confidence = sentiment.get('sentiment_confidence', 50)
        
        # Calculate signal weights based on confidence and data quality
        rsi_weight = min(rsi_confidence / 100, 0.9)
        sentiment_weight = min((sentiment_confidence / 100) * 0.8, 0.7)  # Slightly lower weight for sentiment
        
        # Market momentum factor from real-time data
        momentum_factor = 1.0
        if market_data and 'change_percent' in market_data:
            change_pct = market_data['change_percent']
            if abs(change_pct) > 3:  # High volatility
                momentum_factor = 1.2
            elif abs(change_pct) > 1:  # Moderate movement
                momentum_factor = 1.1
        
        # Signal scoring (-100 to +100)
        rsi_score = self._signal_to_score(rsi_signal) * rsi_weight
        sentiment_score = self._signal_to_score(sentiment_signal) * sentiment_weight
        
        # Weighted combined score
        total_weight = rsi_weight + sentiment_weight
        if total_weight > 0:
            combined_score = (rsi_score + sentiment_score) / total_weight * momentum_factor
        else:
            combined_score = 0
        
        # Determine final signal and confidence
        final_signal, final_confidence, reasoning = self._score_to_signal(
            combined_score, rsi_signal, sentiment_signal, rsi_confidence, sentiment_confidence
        )
        
        # Create comprehensive result
        result = {
            'symbol': symbol,
            'final_signal': final_signal,
            'final_confidence': final_confidence,
            'reasoning': reasoning,
            'combined_score': combined_score,
            'components': {
                'rsi_ml': {
                    'signal': rsi_signal,
                    'confidence': rsi_confidence,
                    'weight': rsi_weight,
                    'score': rsi_score
                },
                'sentiment': {
                    'signal': sentiment_signal,
                    'confidence': sentiment_confidence,
                    'weight': sentiment_weight,
                    'score': sentiment_score,
                    'article_count': sentiment.get('article_count', 0)
                },
                'market_data': {
                    'current_price': market_data.get('current_price', 0) if market_data else 0,
                    'change_percent': market_data.get('change_percent', 0) if market_data else 0,
                    'momentum_factor': momentum_factor
                }
            },
            'timestamp': datetime.now().isoformat(),
            'strategy_version': 'Combined_AI_v1.0'
        }
        
        # Display results
        self._display_analysis_results(result)
        
        return result
    
    def _normalize_sentiment_signal(self, sentiment_signal: str) -> str:
        """Normalize sentiment signals to standard format"""
        signal_map = {
            'WEAK_BUY': 'BUY',
            'WEAK_SELL': 'SELL',
            'BULLISH': 'BUY',
            'BEARISH': 'SELL',
            'NEUTRAL': 'HOLD'
        }
        return signal_map.get(sentiment_signal, sentiment_signal)
    
    def _signal_to_score(self, signal: str) -> float:
        """Convert signal to numerical score (-100 to +100)"""
        score_map = {
            'STRONG_BUY': 100,
            'BUY': 70,
            'WEAK_BUY': 40,
            'HOLD': 0,
            'WEAK_SELL': -40,
            'SELL': -70,
            'STRONG_SELL': -100
        }
        return score_map.get(signal, 0)
    
    def _score_to_signal(self, score: float, rsi_signal: str, sentiment_signal: str, 
                        rsi_conf: float, sentiment_conf: float) -> Tuple[str, float, str]:
        """Convert combined score back to signal with reasoning"""
        
        # Determine signal based on score
        if score > 60:
            signal = 'STRONG_BUY'
            confidence = min(95, abs(score) + 20)
        elif score > 30:
            signal = 'BUY'
            confidence = min(90, abs(score) + 15)
        elif score > 10:
            signal = 'WEAK_BUY'
            confidence = min(80, abs(score) + 50)
        elif score < -60:
            signal = 'STRONG_SELL'
            confidence = min(95, abs(score) + 20)
        elif score < -30:
            signal = 'SELL'
            confidence = min(90, abs(score) + 15)
        elif score < -10:
            signal = 'WEAK_SELL'
            confidence = min(80, abs(score) + 50)
        else:
            signal = 'HOLD'
            confidence = 50 + abs(score)
        
        # Create reasoning
        if rsi_signal == sentiment_signal and rsi_signal != 'HOLD':
            reasoning = f"RSI/ML and Sentiment both suggest {rsi_signal} - Strong consensus"
        elif abs(score) > 40:
            stronger_signal = rsi_signal if rsi_conf > sentiment_conf else sentiment_signal
            reasoning = f"Strong {stronger_signal} signal dominates (Score: {score:.1f})"
        elif rsi_signal != 'HOLD' and sentiment_signal != 'HOLD':
            reasoning = f"Mixed signals: RSI/ML says {rsi_signal}, Sentiment says {sentiment_signal}"
        elif rsi_signal != 'HOLD':
            reasoning = f"Based primarily on technical analysis: {rsi_signal}"
        elif sentiment_signal != 'HOLD':
            reasoning = f"Based primarily on news sentiment: {sentiment_signal}"
        else:
            reasoning = "No clear directional signals from any component"
        
        return signal, confidence, reasoning
    
    def _display_analysis_results(self, result: Dict):
        """Display comprehensive analysis results"""
        print(f"\n🎯 ULTIMATE AI TRADING DECISION FOR {result['symbol']}")
        print("=" * 60)
        
        # Final recommendation
        signal = result['final_signal']
        confidence = result['final_confidence']
        
        signal_emoji = {
            'STRONG_BUY': '🟢🟢', 'BUY': '🟢', 'WEAK_BUY': '🔵',
            'HOLD': '🟡', 'WEAK_SELL': '🟠', 'SELL': '🔴', 'STRONG_SELL': '🔴🔴'
        }
        
        print(f"{signal_emoji.get(signal, '❓')} FINAL SIGNAL: {signal}")
        print(f"📊 CONFIDENCE: {confidence:.1f}%")
        print(f"💡 REASONING: {result['reasoning']}")
        print(f"📈 COMBINED SCORE: {result['combined_score']:.1f}")
        
        # Component breakdown
        print(f"\n🔍 COMPONENT ANALYSIS:")
        rsi_comp = result['components']['rsi_ml']
        sent_comp = result['components']['sentiment']
        market_comp = result['components']['market_data']
        
        print(f"   📊 RSI/ML: {rsi_comp['signal']} ({rsi_comp['confidence']:.1f}%) [Weight: {rsi_comp['weight']:.2f}]")
        print(f"   📰 Sentiment: {sent_comp['signal']} ({sent_comp['confidence']:.1f}% from {sent_comp['article_count']} articles)")
        print(f"   💰 Price: ${market_comp['current_price']:.2f} ({market_comp['change_percent']:+.1f}%)")
        
        print("=" * 60)
    
    def analyze_portfolio(self, symbols: List[str], train_ml: bool = True) -> Dict:
        """Analyze entire portfolio with ultimate AI strategy"""
        print("🚀 ULTIMATE AI PORTFOLIO ANALYSIS")
        print("=" * 70)
        print(f"📊 Analyzing {len(symbols)} symbols with full AI suite")
        print(f"🧠 ML Training: {'Enabled' if train_ml else 'Disabled'}")
        print()
        
        portfolio_results = {}
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] 🎯 Analyzing {symbol}...")
            
            try:
                # Train ML model if requested
                if train_ml:
                    self.rsi_strategy.train_ml_model(symbol)
                
                # Generate ultimate signal
                signal_result = self.generate_ultimate_signal(symbol)
                portfolio_results[symbol] = signal_result
                
                print(f"✅ {symbol}: {signal_result['final_signal']} ({signal_result['final_confidence']:.1f}%)")
                
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                portfolio_results[symbol] = {
                    'symbol': symbol,
                    'final_signal': 'ERROR',
                    'error': str(e)
                }
        
        # Create portfolio summary
        portfolio_summary = self._create_portfolio_summary(portfolio_results)
        
        # Store portfolio analysis in Redis
        if self.redis_client.is_connected():
            self.redis_client.redis_client.set(
                "portfolio_analysis",
                json.dumps(portfolio_summary, default=str),
                ex=3600  # 1 hour
            )
        
        return portfolio_summary
    
    def _create_portfolio_summary(self, results: Dict) -> Dict:
        """Create comprehensive portfolio summary"""
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        
        if not valid_results:
            return {'error': 'No valid results'}
        
        # Categorize signals
        signal_counts = {}
        high_confidence_picks = []
        
        for symbol, result in valid_results.items():
            signal = result['final_signal']
            confidence = result['final_confidence']
            
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            if confidence > 75:
                high_confidence_picks.append({
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': confidence,
                    'reasoning': result['reasoning']
                })
        
        # Sort high confidence picks
        high_confidence_picks.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Calculate portfolio metrics
        avg_confidence = np.mean([r['final_confidence'] for r in valid_results.values()])
        
        buy_signals = [r for r in valid_results.values() if 'BUY' in r['final_signal']]
        sell_signals = [r for r in valid_results.values() if 'SELL' in r['final_signal']]
        
        summary = {
            'total_stocks': len(results),
            'successful_analysis': len(valid_results),
            'average_confidence': avg_confidence,
            'signal_distribution': signal_counts,
            'high_confidence_picks': high_confidence_picks,
            'buy_recommendations': len(buy_signals),
            'sell_recommendations': len(sell_signals),
            'top_picks': high_confidence_picks[:5],
            'portfolio_results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def display_portfolio_summary(self, summary: Dict):
        """Display beautiful portfolio summary"""
        print("\n" + "=" * 70)
        print("🏆 ULTIMATE AI PORTFOLIO RECOMMENDATIONS")
        print("=" * 70)
        
        if 'error' in summary:
            print("❌ No valid analysis results")
            return
        
        print(f"📊 Portfolio Statistics:")
        print(f"   Stocks Analyzed: {summary['successful_analysis']}/{summary['total_stocks']}")
        print(f"   Average Confidence: {summary['average_confidence']:.1f}%")
        print(f"   Buy Recommendations: {summary['buy_recommendations']}")
        print(f"   Sell Recommendations: {summary['sell_recommendations']}")
        
        print(f"\n📈 Signal Distribution:")
        for signal, count in summary['signal_distribution'].items():
            print(f"   {signal}: {count} stocks")
        
        print(f"\n⭐ TOP 5 HIGH-CONFIDENCE PICKS:")
        for i, pick in enumerate(summary['top_picks'], 1):
            signal_emoji = {
                'STRONG_BUY': '🟢🟢', 'BUY': '🟢', 'WEAK_BUY': '🔵',
                'HOLD': '🟡', 'WEAK_SELL': '🟠', 'SELL': '🔴', 'STRONG_SELL': '🔴🔴'
            }
            emoji = signal_emoji.get(pick['signal'], '❓')
            print(f"   {i}. {emoji} {pick['symbol']}: {pick['signal']} ({pick['confidence']:.1f}%)")
            print(f"      💡 {pick['reasoning']}")
        
        print("\n" + "=" * 70)
        print("🚀 Analysis powered by: RSI + ML + News Sentiment + Real-time Data")
        print("=" * 70)


def main():
    """Run the ultimate AI trading strategy"""
    print("🚀 ULTIMATE AI TRADING SYSTEM")
    print("=" * 50)
    print("🧠 Combining: Technical Analysis + Machine Learning + News Sentiment")
    print()
    
    # Initialize the ultimate strategy
    strategy = CombinedTradingStrategy()
    
    # Test portfolio
    portfolio = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMZN"]
    
    print(f"🎯 Testing Ultimate AI Strategy on: {', '.join(portfolio)}")
    print("⏳ This may take a few minutes to analyze news and train ML models...")
    print()
    
    # Run complete portfolio analysis
    results = strategy.analyze_portfolio(portfolio, train_ml=True)
    
    # Display results
    strategy.display_portfolio_summary(results)
    
    # Save results
    with open("ultimate_ai_signals.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Complete analysis saved to ultimate_ai_signals.json")
    print("✅ Ultimate AI Trading Strategy execution completed!")


if __name__ == "__main__":
    main()