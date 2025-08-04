import SwiftUI

struct ChartsView: View {
    @StateObject private var portfolioService = PortfolioService()
    @State private var selectedStock = "AAPL"
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Stock Selector
                stockSelector
                
                // Main Chart Area (Placeholder)
                mainChartArea
                
                // Technical Indicators
                technicalIndicators
                
                Spacer()
            }
            .navigationTitle("Charts")
            .navigationBarTitleDisplayMode(.large)
        }
    }
    
    private var stockSelector: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(portfolioService.watchlistSymbols, id: \.self) { symbol in
                    StockChip(
                        symbol: symbol,
                        isSelected: selectedStock == symbol,
                        stock: portfolioService.getStock(for: symbol)
                    ) {
                        selectedStock = symbol
                    }
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 8)
    }
    
    private var mainChartArea: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let stock = portfolioService.getStock(for: selectedStock) {
                HStack {
                    VStack(alignment: .leading) {
                        Text(selectedStock)
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        Text(stock.formattedPrice)
                            .font(.title3)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing) {
                        HStack {
                            Image(systemName: stock.changeIcon)
                            Text(stock.formattedChange)
                        }
                        .font(.subheadline)
                        .foregroundColor(stock.changeColor)
                    }
                }
                .padding(.horizontal)
            }
            
            // Placeholder for chart
            VStack {
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .font(.system(size: 50))
                    .foregroundColor(.secondary)
                
                Text("Chart Coming Soon")
                    .font(.headline)
                    .foregroundColor(.secondary)
                
                Text("Real-time price charts will be available in the next update")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            .frame(height: 200)
            .frame(maxWidth: .infinity)
        }
        .padding(.vertical)
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .padding(.horizontal)
    }
    
    private var technicalIndicators: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Technical Indicators")
                .font(.headline)
                .fontWeight(.semibold)
                .padding(.horizontal)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 12) {
                IndicatorCard(title: "RSI", value: "45.2", status: "Neutral", color: .yellow)
                IndicatorCard(title: "MACD", value: "1.25", status: "Bullish", color: .green)
                IndicatorCard(title: "Volume", value: "2.1M", status: "Above Avg", color: .blue)
                IndicatorCard(title: "Support", value: "$148.50", status: "Strong", color: .green)
            }
            .padding(.horizontal)
        }
    }
}

struct StockChip: View {
    let symbol: String
    let isSelected: Bool
    let stock: Stock?
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Text(symbol)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                if let stock = stock {
                    Text(stock.formattedPrice)
                        .font(.caption2)
                    
                    Text("\(stock.changePercent, specifier: "%+.1f")%")
                        .font(.caption2)
                        .foregroundColor(stock.changeColor)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(isSelected ? Color.blue : Color(.systemGray5))
            .foregroundColor(isSelected ? .white : .primary)
            .cornerRadius(12)
        }
    }
}

struct IndicatorCard: View {
    let title: String
    let value: String
    let status: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(value)
                .font(.headline)
                .fontWeight(.bold)
            
            Text(status)
                .font(.caption)
                .foregroundColor(color)
                .padding(.horizontal, 8)
                .padding(.vertical, 2)
                .background(color.opacity(0.2))
                .cornerRadius(4)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemBackground))
        .cornerRadius(8)
        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
    }
}

#Preview {
    ChartsView()
}