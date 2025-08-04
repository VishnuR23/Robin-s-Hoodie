import Foundation
import Combine

class APIService: ObservableObject {
    static let shared = APIService()
    
    private let baseURL = "http://localhost:8000" // Python FastAPI server
    private let redisHost = "localhost"
    private let redisPort = 6379
    
    private var cancellables = Set<AnyCancellable>()
    
    private init() {}
    
    // MARK: - Stock Data Methods
    
    func fetchStock(symbol: String) -> AnyPublisher<Stock, Error> {
        let url = URL(string: "\(baseURL)/api/stock/\(symbol)")!
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map(\.data)
            .decode(type: Stock.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    func fetchMultipleStocks(symbols: [String]) -> AnyPublisher<[Stock], Error> {
        let symbolsString = symbols.joined(separator: ",")
        let url = URL(string: "\(baseURL)/api/stocks?symbols=\(symbolsString)")!
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map(\.data)
            .decode(type: [Stock].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    // MARK: - Mock Data for Testing (Remove in production)
    func getMockStocks() -> [Stock] {
        return [
            Stock(symbol: "AAPL", currentPrice: 150.25, previousClose: 148.50, 
                  change: 1.75, changePercent: 1.18, dayHigh: 151.30, 
                  dayLow: 149.10, volume: 45678900, timestamp: ISO8601DateFormatter().string(from: Date())),
            
            Stock(symbol: "GOOGL", currentPrice: 2745.50, previousClose: 2780.00, 
                  change: -34.50, changePercent: -1.24, dayHigh: 2760.00, 
                  dayLow: 2730.00, volume: 1234567, timestamp: ISO8601DateFormatter().string(from: Date())),
            
            Stock(symbol: "TSLA", currentPrice: 245.80, previousClose: 240.20, 
                  change: 5.60, changePercent: 2.33, dayHigh: 248.90, 
                  dayLow: 242.10, volume: 28901234, timestamp: ISO8601DateFormatter().string(from: Date()))
        ]
    }
    
    func getMockAISignals() -> [AITradingSignal] {
        return [
            AITradingSignal(symbol: "AAPL", finalSignal: "STRONG_BUY", finalConfidence: 87.3, 
                           reasoning: "RSI/ML and Sentiment both suggest BUY - Strong consensus", 
                           combinedScore: 78.5, timestamp: ISO8601DateFormatter().string(from: Date()),
                           rsiSignal: "BUY", rsiConfidence: 82.1, 
                           sentimentSignal: "BUY", sentimentConfidence: 84.7, articleCount: 15),
            
            AITradingSignal(symbol: "GOOGL", finalSignal: "HOLD", finalConfidence: 55.2, 
                           reasoning: "Mixed signals: RSI/ML says BUY, Sentiment says SELL", 
                           combinedScore: 12.3, timestamp: ISO8601DateFormatter().string(from: Date()),
                           rsiSignal: "BUY", rsiConfidence: 68.4, 
                           sentimentSignal: "SELL", sentimentConfidence: 71.2, articleCount: 8)
        ]
    }
}

// MARK: - Notification Extensions
extension Notification.Name {
    static let newAISignal = Notification.Name("newAISignal")
    static let portfolioUpdated = Notification.Name("portfolioUpdated")
    static let stockPriceUpdated = Notification.Name("stockPriceUpdated")
}