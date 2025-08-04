import requests
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from textblob import TextBlob
from collections import defaultdict
import yfinance as yf
import feedparser

# Import our Redis client
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data_bridge.redis_data_client import RedisDataClient

class NewsSentimentAnalyzer:
    """
    Advanced News Sentiment Analysis for Trading
    - Scrapes financial news from multiple sources
    - Analyzes sentiment using NLP
    - Correlates sentiment with stock movements
    - Stores results in Redis for trading strategies
    """
    
    def __init__(self):
        self.redis_client = RedisDataClient()
        self.news_sources = {
            'yahoo_finance': 'https://feeds.finance.yahoo.com/rss/2.0/headline',
            'reuters_business': 'http://feeds.reuters.com/reuters/businessNews',
            'cnbc': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664',
            'marketwatch': 'http://feeds.marketwatch.com/marketwatch/marketpulse/'
        }
        
        # Sentiment keywords for financial context
        self.bullish_keywords = [
            'growth', 'profit', 'earnings beat', 'upgrade', 'bullish', 'positive outlook',
            'strong performance', 'record high', 'expansion', 'breakthrough', 'acquisition',
            'merger', 'dividend increase', 'buyback', 'innovation', 'partnership'
        ]
        
        self.bearish_keywords = [
            'loss', 'decline', 'downgrade', 'bearish', 'negative outlook', 'weak performance',
            'lawsuit', 'investigation', 'recession', 'bankruptcy', 'layoffs', 'scandal',
            'controversy', 'volatility', 'crash', 'correction', 'selloff'
        ]
        
        print("📰 News Sentiment Analyzer initialized")
        print(f"🔗 Redis Connection: {'✅' if self.redis_client.is_connected() else '❌'}")
        print(f"📡 News Sources: {len(self.news_sources)} configured")
    
    def scrape_financial_news(self, hours_back: int = 24) -> List[Dict]:
        """Scrape news from multiple financial sources"""
        print(f"📡 Scraping financial news from last {hours_back} hours...")
        
        all_articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        for source_name, rss_url in self.news_sources.items():
            try:
                print(f"📰 Scraping {source_name}...")
                
                # Parse RSS feed
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    # Skip old articles
                    if pub_date and pub_date < cutoff_time:
                        continue
                    
                    article = {
                        'title': entry.get('title', ''),
                        'description': entry.get('description', ''),
                        'link': entry.get('link', ''),
                        'source': source_name,
                        'published_date': pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                        'raw_content': f"{entry.get('title', '')} {entry.get('description', '')}"
                    }
                    
                    all_articles.append(article)
                
                print(f"✅ Found {len([a for a in all_articles if a['source'] == source_name])} articles from {source_name}")
                time.sleep(1)  # Be respectful to news sites
                
            except Exception as e:
                print(f"❌ Error scraping {source_name}: {e}")
        
        print(f"📰 Total articles collected: {len(all_articles)}")
        return all_articles
    
    def get_stock_specific_news(self, symbol: str, hours_back: int = 24) -> List[Dict]:
        """Get news specifically mentioning a stock symbol or company"""
        print(f"🔍 Finding news for {symbol}...")
        
        # Get company name for better matching
        try:
            ticker = yf.Ticker(symbol)
            company_info = ticker.info
            company_name = company_info.get('longName', symbol)
            short_name = company_info.get('shortName', symbol)
        except:
            company_name = symbol
            short_name = symbol
        
        # Scrape all news
        all_news = self.scrape_financial_news(hours_back)
        
        # Filter for stock-specific news
        relevant_news = []
        search_terms = [symbol.upper(), company_name, short_name]
        
        for article in all_news:
            content = article['raw_content'].upper()
            
            # Check if any search term appears in the content
            if any(term.upper() in content for term in search_terms):
                article['relevance_score'] = self._calculate_relevance(article['raw_content'], search_terms)
                article['stock_symbol'] = symbol
                relevant_news.append(article)
        
        print(f"📰 Found {len(relevant_news)} articles mentioning {symbol}")
        return relevant_news
    
    def _calculate_relevance(self, text: str, search_terms: List[str]) -> float:
        """Calculate how relevant an article is to the stock"""
        text_upper = text.upper()
        relevance = 0
        
        for term in search_terms:
            count = text_upper.count(term.upper())
            relevance += count * (len(term) / 10)  # Longer terms get higher weight
        
        return min(relevance, 1.0)  # Cap at 1.0
    
    def analyze_sentiment(self, articles: List[Dict]) -> Dict:
        """Analyze sentiment of news articles using multiple methods"""
        print(f"🧠 Analyzing sentiment of {len(articles)} articles...")
        
        if not articles:
            return self._empty_sentiment_result()
        
        sentiments = []
        weighted_sentiments = []
        
        for article in articles:
            content = article['raw_content']
            
            # Method 1: TextBlob sentiment analysis
            blob = TextBlob(content)
            polarity = blob.sentiment.polarity  # -1 (negative) to 1 (positive)
            subjectivity = blob.sentiment.subjectivity  # 0 (objective) to 1 (subjective)
            
            # Method 2: Financial keyword analysis
            keyword_sentiment = self._analyze_financial_keywords(content)
            
            # Method 3: Title vs content weighting (titles are more important)
            title_sentiment = TextBlob(article['title']).sentiment.polarity
            
            # Combine sentiments with weights
            combined_sentiment = (
                0.4 * polarity +           # TextBlob general sentiment
                0.3 * keyword_sentiment +  # Financial-specific keywords
                0.3 * title_sentiment      # Title sentiment (important for news)
            )
            
            # Weight by relevance score if available
            relevance = article.get('relevance_score', 1.0)
            weighted_sentiment = combined_sentiment * relevance
            
            sentiments.append(combined_sentiment)
            weighted_sentiments.append(weighted_sentiment)
            
            # Store individual article analysis
            article['sentiment'] = {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'keyword_sentiment': keyword_sentiment,
                'combined_sentiment': combined_sentiment,
                'weighted_sentiment': weighted_sentiment
            }
        
        # Calculate aggregate metrics
        avg_sentiment = np.mean(sentiments)
        weighted_avg_sentiment = np.mean(weighted_sentiments)
        sentiment_std = np.std(sentiments)
        
        # Classify overall sentiment
        if weighted_avg_sentiment > 0.1:
            overall_sentiment = "BULLISH"
            confidence = min(95, abs(weighted_avg_sentiment) * 100 + 60)
        elif weighted_avg_sentiment < -0.1:
            overall_sentiment = "BEARISH"
            confidence = min(95, abs(weighted_avg_sentiment) * 100 + 60)
        else:
            overall_sentiment = "NEUTRAL"
            confidence = 50
        
        # Count sentiment distribution
        positive_count = len([s for s in sentiments if s > 0.05])
        negative_count = len([s for s in sentiments if s < -0.05])
        neutral_count = len(sentiments) - positive_count - negative_count
        
        result = {
            'overall_sentiment': overall_sentiment,
            'confidence': confidence,
            'average_sentiment': avg_sentiment,
            'weighted_average_sentiment': weighted_avg_sentiment,
            'sentiment_std': sentiment_std,
            'article_count': len(articles),
            'positive_articles': positive_count,
            'negative_articles': negative_count,
            'neutral_articles': neutral_count,
            'sentiment_distribution': {
                'positive': positive_count / len(articles),
                'negative': negative_count / len(articles),
                'neutral': neutral_count / len(articles)
            },
            'articles': articles,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"📊 Sentiment Analysis Complete:")
        print(f"   Overall: {overall_sentiment} ({confidence:.1f}% confidence)")
        print(f"   Distribution: {positive_count} positive, {negative_count} negative, {neutral_count} neutral")
        
        return result
    
    def _analyze_financial_keywords(self, text: str) -> float:
        """Analyze sentiment based on financial-specific keywords"""
        text_lower = text.lower()
        
        bullish_score = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
        bearish_score = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
        
        total_keywords = bullish_score + bearish_score
        if total_keywords == 0:
            return 0.0
        
        # Return score between -1 and 1
        return (bullish_score - bearish_score) / max(total_keywords, 1)
    
    def _empty_sentiment_result(self) -> Dict:
        """Return empty sentiment result when no articles found"""
        return {
            'overall_sentiment': 'NEUTRAL',
            'confidence': 0,
            'average_sentiment': 0.0,
            'weighted_average_sentiment': 0.0,
            'sentiment_std': 0.0,
            'article_count': 0,
            'positive_articles': 0,
            'negative_articles': 0,
            'neutral_articles': 0,
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 1},
            'articles': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_stock_sentiment(self, symbol: str, hours_back: int = 24) -> Dict:
        """Complete sentiment analysis for a specific stock"""
        print(f"\n🎯 Complete sentiment analysis for {symbol}")
        print("=" * 50)
        
        # Get stock-specific news
        news_articles = self.get_stock_specific_news(symbol, hours_back)
        
        # Analyze sentiment
        sentiment_result = self.analyze_sentiment(news_articles)
        sentiment_result['symbol'] = symbol
        
        # Store in Redis for trading strategies to use
        if self.redis_client.is_connected():
            redis_key = f"sentiment:{symbol}"
            self.redis_client.redis_client.set(
                redis_key, 
                json.dumps(sentiment_result, default=str),
                ex=3600  # Expire after 1 hour
            )
            print(f"💾 Stored sentiment analysis in Redis: {redis_key}")
        
        return sentiment_result
    
    def analyze_market_sentiment(self, symbols: List[str], hours_back: int = 24) -> Dict:
        """Analyze overall market sentiment across multiple stocks"""
        print(f"\n📊 Analyzing market sentiment for {len(symbols)} stocks")
        print("=" * 60)
        
        stock_sentiments = {}
        all_articles = []
        
        for symbol in symbols:
            print(f"\n📈 Analyzing {symbol}...")
            sentiment = self.analyze_stock_sentiment(symbol, hours_back)
            stock_sentiments[symbol] = sentiment
            all_articles.extend(sentiment['articles'])
            time.sleep(0.5)  # Rate limiting
        
        # Calculate market-wide sentiment
        overall_sentiments = [s['weighted_average_sentiment'] for s in stock_sentiments.values() if s['article_count'] > 0]
        
        if overall_sentiments:
            market_sentiment = np.mean(overall_sentiments)
            market_confidence = np.mean([s['confidence'] for s in stock_sentiments.values()])
            
            if market_sentiment > 0.1:
                market_mood = "BULLISH"
            elif market_sentiment < -0.1:
                market_mood = "BEARISH"
            else:
                market_mood = "NEUTRAL"
        else:
            market_sentiment = 0.0
            market_confidence = 0.0
            market_mood = "NEUTRAL"
        
        market_result = {
            'market_sentiment': market_mood,
            'market_score': market_sentiment,
            'market_confidence': market_confidence,
            'total_articles': len(all_articles),
            'stocks_analyzed': len(symbols),
            'stock_sentiments': stock_sentiments,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store market sentiment in Redis
        if self.redis_client.is_connected():
            self.redis_client.redis_client.set(
                "market_sentiment", 
                json.dumps(market_result, default=str),
                ex=3600
            )
        
        return market_result
    
    def get_sentiment_trading_signal(self, symbol: str) -> Dict:
        """Generate trading signal based on sentiment analysis"""
        print(f"🎯 Generating sentiment-based trading signal for {symbol}")
        
        # Get sentiment analysis
        sentiment = self.analyze_stock_sentiment(symbol)
        
        # Generate trading signal based on sentiment
        if sentiment['overall_sentiment'] == 'BULLISH' and sentiment['confidence'] > 70:
            signal = 'BUY'
            reason = f"Strong positive sentiment ({sentiment['confidence']:.1f}% confidence)"
        elif sentiment['overall_sentiment'] == 'BEARISH' and sentiment['confidence'] > 70:
            signal = 'SELL'
            reason = f"Strong negative sentiment ({sentiment['confidence']:.1f}% confidence)"
        elif sentiment['overall_sentiment'] == 'BULLISH' and sentiment['confidence'] > 60:
            signal = 'WEAK_BUY'
            reason = f"Moderate positive sentiment ({sentiment['confidence']:.1f}% confidence)"
        elif sentiment['overall_sentiment'] == 'BEARISH' and sentiment['confidence'] > 60:
            signal = 'WEAK_SELL'
            reason = f"Moderate negative sentiment ({sentiment['confidence']:.1f}% confidence)"
        else:
            signal = 'HOLD'
            reason = f"Neutral sentiment or low confidence ({sentiment['confidence']:.1f}%)"
        
        trading_signal = {
            'symbol': symbol,
            'sentiment_signal': signal,
            'sentiment_confidence': sentiment['confidence'],
            'reason': reason,
            'article_count': sentiment['article_count'],
            'sentiment_score': sentiment['weighted_average_sentiment'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Store trading signal in Redis
        if self.redis_client.is_connected():
            self.redis_client.redis_client.set(
                f"sentiment_signal:{symbol}",
                json.dumps(trading_signal, default=str),
                ex=1800  # 30 minutes
            )
        
        print(f"📡 Sentiment Signal: {signal} - {reason}")
        return trading_signal


def main():
    """Test the sentiment analysis system"""
    print("📰 NEWS SENTIMENT ANALYSIS SYSTEM")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = NewsSentimentAnalyzer()
    
    # Test symbols
    test_symbols = ["AAPL", "GOOGL", "TSLA", "MSFT"]
    
    print(f"\n🎯 Testing sentiment analysis for: {', '.join(test_symbols)}")
    
    # Analyze market sentiment
    market_sentiment = analyzer.analyze_market_sentiment(test_symbols, hours_back=48)
    
    print(f"\n📊 MARKET SENTIMENT SUMMARY:")
    print(f"Overall Market Mood: {market_sentiment['market_sentiment']}")
    print(f"Market Confidence: {market_sentiment['market_confidence']:.1f}%")
    print(f"Total Articles Analyzed: {market_sentiment['total_articles']}")
    
    # Generate trading signals
    print(f"\n🎯 SENTIMENT TRADING SIGNALS:")
    for symbol in test_symbols:
        signal = analyzer.get_sentiment_trading_signal(symbol)
        print(f"   {symbol}: {signal['sentiment_signal']} - {signal['reason']}")
    
    print(f"\n✅ Sentiment analysis complete!")
    print(f"💾 All results stored in Redis for trading strategies to use")


if __name__ == "__main__":
    main()