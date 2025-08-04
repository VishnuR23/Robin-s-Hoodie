import SwiftUI

struct TradingSignalsView: View {
    @StateObject private var portfolioService = PortfolioService()
    @State private var selectedSignal: AITradingSignal?
    @State private var showingSignalDetail = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // AI Status Header
                aiStatusHeader
                
                // Signals List
                signalsList
            }
            .navigationTitle("AI Signals")
            .navigationBarTitleDisplayMode(.large)
            .refreshable {
                portfolioService.refreshAllData()
            }
        }
        .sheet(item: $selectedSignal) { signal in
            AISignalDetailView(signal: signal)
        }
    }
    
    // MARK: - AI Status Header
    private var aiStatusHeader: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .font(.title2)
                    .foregroundColor(.blue)
                Text("AI Trading Intelligence")
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
                
                Circle()
                    .fill(.green)
                    .frame(width: 8, height: 8)
                Text("Live")
                    .font(.caption)
                    .foregroundColor(.green)
            }
            
            HStack(spacing: 20) {
                StatPill(title: "Total Signals", value: "\(portfolioService.aiSignals.count)")
                StatPill(title: "High Confidence", value: "\(portfolioService.aiSignals.filter { $0.finalConfidence > 75 }.count)")
                StatPill(title: "Buy Signals", value: "\(portfolioService.aiSignals.filter { $0.finalSignal.contains("BUY") }.count)")
            }
            
            Text("Powered by RSI + ML + News Sentiment Analysis")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .padding(.horizontal)
    }
    
    // MARK: - Signals List
    private var signalsList: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                if portfolioService.aiSignals.isEmpty {
                    EmptySignalsView()
                } else {
                    ForEach(portfolioService.aiSignals) { signal in
                        AISignalRowView(signal: signal) {
                            selectedSignal = signal
                            showingSignalDetail = true
                        }
                    }
                }
            }
            .padding()
        }
    }
}

// MARK: - Supporting Views

struct StatPill: View {
    let title: String
    let value: String
    
    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.headline)
                .fontWeight(.bold)
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color(.systemBackground))
        .cornerRadius(16)
    }
}

struct AISignalRowView: View {
    let signal: AITradingSignal
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 16) {
                // Signal Icon and Symbol
                VStack(spacing: 4) {
                    Image(systemName: signal.signalIcon)
                        .font(.title2)
                        .foregroundColor(signal.signalColor)
                    
                    Text(signal.symbol)
                        .font(.caption)
                        .fontWeight(.semibold)
                }
                .frame(width: 60)
                
                // Signal Details
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(signal.finalSignal)
                            .font(.headline)
                            .fontWeight(.semibold)
                            .foregroundColor(signal.signalColor)
                        
                        Spacer()
                        
                        ConfidenceBadge(confidence: signal.finalConfidence)
                    }
                    
                    Text(signal.reasoning)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                    
                    HStack {
                        if let articleCount = signal.articleCount {
                            Label("\(articleCount) articles", systemImage: "newspaper")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Text("2m ago")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
                
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.05), radius: 3, x: 0, y: 1)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct ConfidenceBadge: View {
    let confidence: Double
    
    private var badgeColor: Color {
        switch confidence {
        case 80...100: return .green
        case 70..<80: return .blue
        case 60..<70: return .orange
        default: return .red
        }
    }
    
    var body: some View {
        Text("\(confidence, specifier: "%.1f")%")
            .font(.caption2)
            .fontWeight(.semibold)
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(badgeColor)
            .cornerRadius(8)
    }
}

struct EmptySignalsView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 50))
                .foregroundColor(.secondary)
            
            Text("No AI Signals")
                .font(.headline)
                .fontWeight(.semibold)
            
            Text("The AI is analyzing market conditions. Check back soon for new trading signals.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding(.vertical, 40)
    }
}

struct AISignalDetailView: View {
    let signal: AITradingSignal
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Signal Header
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text(signal.symbol)
                                .font(.largeTitle)
                                .fontWeight(.bold)
                            
                            Spacer()
                            
                            Image(systemName: signal.signalIcon)
                                .font(.largeTitle)
                                .foregroundColor(signal.signalColor)
                        }
                        
                        HStack {
                            Text(signal.finalSignal)
                                .font(.title2)
                                .fontWeight(.semibold)
                                .foregroundColor(signal.signalColor)
                            
                            Spacer()
                            
                            VStack(alignment: .trailing) {
                                Text("\(signal.finalConfidence, specifier: "%.1f")%")
                                    .font(.title2)
                                    .fontWeight(.bold)
                                Text("Confidence")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    
                    // Reasoning
                    VStack(alignment: .leading, spacing: 12) {
                        Text("AI Reasoning")
                            .font(.headline)
                            .fontWeight(.semibold)
                        
                        Text(signal.reasoning)
                            .font(.body)
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(8)
                    }
                }
                .padding()
            }
            .navigationTitle("AI Signal Details")
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
    TradingSignalsView()
}