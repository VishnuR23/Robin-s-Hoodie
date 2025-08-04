import SwiftUI

struct SettingsView: View {
    @State private var notificationsEnabled = true
    @State private var riskTolerance: Double = 5
    @State private var autoTradingEnabled = false
    @State private var selectedTheme = "Dark"
    
    let themes = ["Light", "Dark", "System"]
    
    var body: some View {
        NavigationView {
            Form {
                // Profile Section
                Section("Profile") {
                    HStack {
                        Image(systemName: "person.circle.fill")
                            .font(.largeTitle)
                            .foregroundColor(.blue)
                        
                        VStack(alignment: .leading) {
                            Text("AI Trader")
                                .font(.headline)
                            Text("Premium Account")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Button("Edit") {
                            // Edit profile action
                        }
                    }
                }
                
                // Trading Preferences
                Section("Trading Preferences") {
                    HStack {
                        Image(systemName: "slider.horizontal.3")
                            .foregroundColor(.orange)
                        Text("Risk Tolerance")
                        Spacer()
                        Text("\(Int(riskTolerance))/10")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(value: $riskTolerance, in: 1...10, step: 1)
                        .accentColor(.orange)
                    
                    Toggle(isOn: $autoTradingEnabled) {
                        HStack {
                            Image(systemName: "bolt.fill")
                                .foregroundColor(.yellow)
                            Text("Auto Trading")
                        }
                    }
                }
                
                // Notifications
                Section("Notifications") {
                    Toggle(isOn: $notificationsEnabled) {
                        HStack {
                            Image(systemName: "bell.fill")
                                .foregroundColor(.red)
                            Text("Push Notifications")
                        }
                    }
                    
                    if notificationsEnabled {
                        HStack {
                            Image(systemName: "brain.head.profile")
                                .foregroundColor(.blue)
                            Text("AI Signal Alerts")
                            Spacer()
                            Text("Enabled")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Image(systemName: "chart.line.uptrend.xyaxis")
                                .foregroundColor(.green)
                            Text("Price Alerts")
                            Spacer()
                            Text("Enabled")
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                // Appearance
                Section("Appearance") {
                    Picker("Theme", selection: $selectedTheme) {
                        ForEach(themes, id: \.self) { theme in
                            Text(theme).tag(theme)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                // AI Configuration
                Section("AI Configuration") {
                    HStack {
                        Image(systemName: "brain")
                            .foregroundColor(.purple)
                        VStack(alignment: .leading) {
                            Text("Model Version")
                            Text("v2.1.0 - Latest")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        Text("Active")
                            .foregroundColor(.green)
                            .font(.caption)
                    }
                    
                    HStack {
                        Image(systemName: "newspaper")
                            .foregroundColor(.blue)
                        Text("News Sources")
                        Spacer()
                        Text("4 Active")
                            .foregroundColor(.secondary)
                    }
                }
                
                // Data & Privacy
                Section("Data & Privacy") {
                    HStack {
                        Image(systemName: "shield.fill")
                            .foregroundColor(.green)
                        Text("Data Encryption")
                        Spacer()
                        Text("Enabled")
                            .foregroundColor(.green)
                    }
                    
                    Button(action: {
                        // Clear cache action
                    }) {
                        HStack {
                            Image(systemName: "trash")
                                .foregroundColor(.red)
                            Text("Clear Cache")
                            Spacer()
                        }
                    }
                }
                
                // About
                Section("About") {
                    HStack {
                        Image(systemName: "info.circle")
                            .foregroundColor(.blue)
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Image(systemName: "questionmark.circle")
                            .foregroundColor(.orange)
                        Text("Help & Support")
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                    
                    HStack {
                        Image(systemName: "star.fill")
                            .foregroundColor(.yellow)
                        Text("Rate App")
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

#Preview {
    SettingsView()
}