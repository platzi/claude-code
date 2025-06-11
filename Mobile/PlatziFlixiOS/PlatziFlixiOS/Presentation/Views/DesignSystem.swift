import SwiftUI

// MARK: - Design System Extensions

extension Color {
    // Primary Colors
    static let primaryBlue = Color(hex: "007AFF")
    static let primaryGreen = Color(hex: "34C759")
    static let primaryRed = Color(hex: "FF3B30")
    
    // Adaptive Neutral Colors - These will automatically adapt to dark mode
    static let neutralBlack = Color.primary
    static let neutralGray900 = Color.primary
    static let neutralGray800 = Color.secondary
    static let neutralGray600 = Color.secondary
    static var neutralGray400: Color { Color.secondary.opacity(0.6) }
    static let neutralGray200 = Color(.systemGray6)
    static let neutralWhite = Color(.systemBackground)
    
    // Semantic Colors - Using system colors for better dark mode support
    static let successGreen = Color(hex: "30D158")
    static let warningOrange = Color(hex: "FF9500")
    static let errorRed = Color(hex: "FF453A")
    static let infoBlue = Color(hex: "64D2FF")
    
    // Card and Surface Colors - Adaptive
    static let cardBackground = Color(.secondarySystemBackground)
    static let surfaceBackground = Color(.systemBackground)
    static let groupedBackground = Color(.systemGroupedBackground)
    
    // Helper initializer for hex colors
    init(hex: String) {
        let scanner = Scanner(string: hex)
        _ = scanner.scanString("#")
        
        var rgbValue: UInt64 = 0
        scanner.scanHexInt64(&rgbValue)
        
        let r = Double((rgbValue & 0xFF0000) >> 16) / 255.0
        let g = Double((rgbValue & 0x00FF00) >> 8) / 255.0
        let b = Double(rgbValue & 0x0000FF) / 255.0
        
        self.init(red: r, green: g, blue: b)
    }
}

// MARK: - Spacing System
struct Spacing {
    static let spacing1: CGFloat = 4.0   // 0.5x
    static let spacing2: CGFloat = 8.0   // 1x
    static let spacing3: CGFloat = 12.0  // 1.5x
    static let spacing4: CGFloat = 16.0  // 2x
    static let spacing5: CGFloat = 20.0  // 2.5x
    static let spacing6: CGFloat = 24.0  // 3x
    static let spacing8: CGFloat = 32.0  // 4x
    static let spacing10: CGFloat = 40.0 // 5x
    static let spacing12: CGFloat = 48.0 // 6x
    static let spacing16: CGFloat = 64.0 // 8x
}

// MARK: - Border Radius
struct Radius {
    static let radiusSmall: CGFloat = 4.0
    static let radiusMedium: CGFloat = 8.0
    static let radiusLarge: CGFloat = 12.0
    static let radiusXLarge: CGFloat = 16.0
    static let radiusFull: CGFloat = 1000.0
}

// MARK: - Typography Extensions
extension Font {
    // Headings
    static let largeTitle = Font.largeTitle.weight(.bold)
    static let title1 = Font.title.weight(.semibold)
    static let title2 = Font.title2.weight(.semibold)
    static let title3 = Font.title3.weight(.medium)
    
    // Body Text
    static let bodyRegular = Font.body.weight(.regular)
    static let bodyEmphasized = Font.body.weight(.medium)
    static let captionRegular = Font.caption.weight(.regular)
    static let caption2Regular = Font.caption2.weight(.regular)
    
    // Interactive
    static let buttonLarge = Font.headline.weight(.semibold)
    static let buttonMedium = Font.body.weight(.medium)
    static let buttonSmall = Font.caption.weight(.medium)
}

// MARK: - Card Style ViewModifier
struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(Color.cardBackground)
            .cornerRadius(Radius.radiusLarge)
            .shadow(color: Color.primary.opacity(0.1), radius: 4, x: 0, y: 2)
    }
}

extension View {
    func cardStyle() -> some View {
        self.modifier(CardStyle())
    }
} 