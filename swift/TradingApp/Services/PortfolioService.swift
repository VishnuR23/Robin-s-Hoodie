import Foundation
import Combine
import SwiftUI

class PortfolioService: ObservableObject {
    @Published var stocks: [Stock] = []
    @Published var aiSignals: [AITradingSignal] = []
    @Published var portfolio: Portfolio?
    @Published var marketOverview: MarketOverview?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private var cancellables = Set<AnyCancellable>()
    private var refreshTimer: Timer?
    
    // Watchlist symbols
    let watchlistSymbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMZN"]
    
    init() {
        loadInitialData()
    }
    
    // MARK: - Public Methods
    
    func startRealTimeUpdates() {
        // Refresh every 30 seconds
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { _ in
            self.refreshAllData()
        }
    }
    
    func stopRealTimeUpdates() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }
    
    func refreshAllData() {
        isLoading = true
        errorMessage = nil
        
        // For now, just reload mock data
        // In production, this would call the real APIs
        loadMockData()
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            self.isLoading = false
        }
    }
    
    // MARK: - Private Methods
    
    private func loadInitialData() {
        // For development, use mock data
        loadMockData()
    }
    
    // MARK: - Mock Data (for development)
    
    private func loadMockData() {
        DispatchQueue.main.async {
            self.stocks = APIService.shared.getMockStocks()
            self.aiSignals = APIService.shared.getMockAISignals()
            self.marketOverview = self.getMockMarketOverview()
            self.portfolio = self.getMockPortfolio()
        }
    }
    
    private func getMockMarketOverview() -> MarketOverview {
        return MarketOverview(
            sp500: MarketIndex(currentPrice: 4150.25, change: 25.30, changePercent: 0.61),
            nasdaq: MarketIndex(currentPrice: 12750.80, change: -45.20, changePercent: -0.35),
            dowJones: MarketIndex(currentPrice: 33500.15, change: 120.45, changePercent: 0.36),
            vix: MarketIndex(currentPrice: 18.25, change: -1.15, changePercent: -5.93)
        )
    }
    
    private func getMockPortfolio() -> Portfolio {
        let positions = [
            Position(symbol: "AAPL", shares: 50, avgCost: 145.00, currentPrice: 150.25, 
                    marketValue: 7512.50, totalGainLoss: 262.50, gainLossPercent: 3.62),
            Position(symbol: "GOOGL", shares: 5, avgCost: 2800.00, currentPrice: 2745.50, 
                    marketValue: 13727.50, totalGainLoss: -272.50, gainLossPercent: -1.95),
            Position(symbol: "TSLA", shares: 25, avgCost: 235.00, currentPrice: 245.80, 
                    marketValue: 6145.00, totalGainLoss: 270.00, gainLossPercent: 4.60)
        ]
        
        let totalValue = positions.reduce(0) { $0 + $1.marketValue }
        let totalGainLoss = positions.reduce(0) { $0 + $1.totalGainLoss }
        let totalChangePercent = (totalGainLoss / (totalValue - totalGainLoss)) * 100
        
        return Portfolio(
            totalValue: totalValue,
            totalChange: totalGainLoss,
            totalChangePercent: totalChangePercent,
            positions: positions,
            lastUpdated: ISO8601DateFormatter().string(from: Date())
        )
    }
    
    // MARK: - Utility Methods
    
    func getAISignal(for symbol: String) -> AITradingSignal? {
        return aiSignals.first { $0.symbol == symbol }
    }
    
    func getStock(for symbol: String) -> Stock? {
        return stocks.first { $0.symbol == symbol }
    }
    
    func getStrongBuySignals() -> [AITradingSignal] {
        return aiSignals.filter { $0.finalSignal.contains("BUY") && $0.finalConfidence > 75 }
    }
    
    deinit {
        stopRealTimeUpdates()
    }
}