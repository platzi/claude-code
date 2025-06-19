//
//  Class.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Domain model representing a class in Platziflix
struct Class: Identifiable, Equatable {
    let id: Int
    let courseId: Int
    let name: String
    let description: String
    let slug: String
    let videoUrl: String?
    let createdAt: Date?
    let updatedAt: Date?
    let deletedAt: Date?
    
    /// Computed property to check if class is active
    var isActive: Bool {
        deletedAt == nil
    }
    
    /// Computed property for display description (truncated if needed)
    var displayDescription: String {
        if description.count > 80 {
            return String(description.prefix(80)) + "..."
        }
        return description
    }
    
    /// Computed property to check if video is available
    var hasVideo: Bool {
        guard let videoUrl = videoUrl else { return false }
        return !videoUrl.isEmpty
    }
    
    /// Computed property for estimated duration (mock for now)
    var estimatedDuration: String {
        return "15 min" // This would come from actual video metadata
    }
}

// MARK: - Mock Data for Preview
extension Class {
    static let mockClasses: [Class] = [
        Class(
            id: 1,
            courseId: 4,
            name: "Introducción a React",
            description: "En esta primera clase aprenderemos qué es React, por qué es tan popular y configuraremos nuestro primer proyecto.",
            slug: "introduccion-a-react",
            videoUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        ),
        Class(
            id: 2,
            courseId: 4,
            name: "Componentes y JSX",
            description: "Aprenderemos a crear nuestros primeros componentes de React utilizando JSX y las mejores prácticas.",
            slug: "componentes-y-jsx",
            videoUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        ),
        Class(
            id: 3,
            courseId: 4,
            name: "Estado y Props",
            description: "Entenderemos cómo manejar el estado de los componentes y cómo pasar información entre ellos usando props.",
            slug: "estado-y-props",
            videoUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        )
    ]
} 