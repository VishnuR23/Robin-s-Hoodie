import SwiftUI

struct PortfolioView: View {
    @StateObject private var portfolioService = PortfolioService()
    @State private var showingStockDetail = false
    @State private var selectedStock: Stock?
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 16) {
                    // Portfolio Header
                    portfolioHeaderView
                    
                    // Market Overview
                    marketOverviewView
                    
                    // Watchlist
                    watchlistView
                    
                    // AI Recommendations
                    aiRecommendationsView
                }
                .padding()
            }
            .navigationTitle("Portfolio")
            .navigationBarTitleDisplayMode(.large)
            .refreshable {
                portfolioService.refreshAllData()
            }
        }
        .sheet(item: $selectedStock) { stock in
            StockDetailView(stock: stock)
        }
    }
    
    // MARK: - Portfolio Header
    private var portfolioHeaderView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Total Portfolio Value")
                    .font(.headline)
                    .foregroundColor(.secondary)
                Spacer()
                Text("Updated now")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if let portfolio = portfolioService.portfolio {
                HStack(alignment: .bottom) {
                    Text(formatCurrency(portfolio.totalValue))
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Spacer()
                    
                    VStack(alignment: .trailing) {
                        HStack {
                            Image(systemName: portfolio.totalChange >= 0 ? "arrow.up.right" : "arrow.down.right")
                            Text(formatCurrency(portfolio.totalChange))
                        }
                        .foregroundColor(portfolio.totalChange >= 0 ? .green : .red)
                        .font(.headline)
                        
                        Text("\(portfolio.totalChangePercent, specifier: "%.2f")%")
                            .foregroundColor(portfolio.totalChange >= 0 ? .green : .red)
                            .font(.subheadline)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    // MARK: - Market Overview
    private var marketOverviewView: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Market Overview")
                .font(.headline)
                .padding(.horizontal)
            
            if let market = portfolioService.marketOverview {
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 12) {
                    MarketIndexCard(title: "S&P 500", index: market.sp500)
                    MarketIndexCard(title: "NASDAQ", index: market.nasdaq)
                    MarketIndexCard(title: "Dow Jones", index: market.dowJones)
                    MarketIndexCard(title: "VIX", index: market.vix)
                }
                .padding(.horizontal)
            }
        }
    }
    
    // MARK: - Watchlist
    private var watchlistView: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Watchlist")
                .font(.headline)
                .padding(.horizontal)
            
            LazyVStack(spacing: 8) {
                ForEach(portfolioService.stocks) { stock in
                    StockRowView(stock: stock) {
                        selectedStock = stock
                        showingStockDetail = true
                    }
                }
            }
            .padding(.horizontal)
        }
    }
    
    // MARK: - AI Recommendations
    private var aiRecommendationsView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(.blue)
                Text("AI Recommendations")
                    .font(.headline)
            }
            .padding(.horizontal)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(portfolioService.getStrongBuySignals()) { signal in
                        AISignalCard(signal: signal)
                    }
                }
                .padding(.horizontal)
            }
        }
    }
    
    private func formatCurrency(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "USD"
        return formatter.string(from: NSNumber(value: value)) ?? "$0.00"
    }
}

// MARK: - Supporting Views

struct MarketIndexCard: View {
    let title: String
    let index: MarketIndex
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(String(format: "%.2f", index.currentPrice))
                .font(.headline)
                .fontWeight(.semibold)
            
            HStack {
                Image(systemName: index.change >= 0 ? "arrow.up.right" : "arrow.down.right")
                    .font(.caption2)
                Text(String(format: "%.2f (%.2f%%)", index.change, index.changePercent))
                    .font(.caption2)
            }
            .foregroundColor(index.changeColor)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemBackground))
        .cornerRadius(8)
        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
    }
}

struct StockRowView: View {
    let stock: Stock
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(stock.symbol)
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    Text(stock.formattedPrice)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    HStack {
                        Image(systemName: stock.changeIcon)
                            .font(.caption2)
                        Text(stock.formattedChange)
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }
                    .foregroundColor(stock.changeColor)
                }
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(8)
            .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct AISignalCard: View {
    let signal: AITradingSignal
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: signal.signalIcon)
                    .foregroundColor(signal.signalColor)
                Text(signal.symbol)
                    .font(.headline)
                    .fontWeight(.semibold)
            }
            
            Text(signal.finalSignal)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(signal.signalColor)
            
            Text("\(signal.finalConfidence, specifier: "%.1f")% confidence")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .frame(width: 150, alignment: .leading)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct StockDetailView: View {
    let stock: Stock
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Text(stock.symbol)
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text(stock.formattedPrice)
                        .font(.title2)
                        .foregroundColor(.secondary)
                    
                    HStack {
                        Image(systemName: stock.changeIcon)
                        Text(stock.formattedChange)
                    }
                    .font(.headline)
                    .foregroundColor(stock.changeColor)
                }
                .padding()
            }
            .navigationTitle("Stock Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    PortfolioView()
}