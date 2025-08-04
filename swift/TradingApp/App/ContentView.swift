import SwiftUI

struct ContentView: View {
    @StateObject private var portfolioService = PortfolioService()
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            // Portfolio Overview Tab
            PortfolioView()
                .tabItem {
                    Image(systemName: "chart.pie.fill")
                    Text("Portfolio")
                }
                .tag(0)
            
            // AI Signals Tab
            TradingSignalsView()
                .tabItem {
                    Image(systemName: "brain.head.profile")
                    Text("AI Signals")
                }
                .tag(1)
            
            // Live Charts Tab
            ChartsView()
                .tabItem {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                    Text("Charts")
                }
                .tag(2)
            
            // Settings Tab
            SettingsView()
                .tabItem {
                    Image(systemName: "gearshape.fill")
                    Text("Settings")
                }
                .tag(3)
        }
        .accentColor(.green) // Trading green theme
        .onAppear {
            // Start data refresh when app launches
            portfolioService.startRealTimeUpdates()
        }
    }
}