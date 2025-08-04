import SwiftUI

@main
struct TradingAppApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.dark) // Trading apps look better in dark mode
        }
    }
}