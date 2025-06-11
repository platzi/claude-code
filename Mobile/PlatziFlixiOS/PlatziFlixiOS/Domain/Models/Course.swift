import Foundation

/// Domain model representing a course in Platziflix
struct Course: Identifiable, Equatable {
    let id: Int
    let name: String
    let description: String
    let thumbnail: String
    let slug: String
    let teacherIds: [Int]
    let createdAt: Date?
    let updatedAt: Date?
    let deletedAt: Date?
    
    /// Computed property to check if course is active
    var isActive: Bool {
        deletedAt == nil
    }
    
    /// Computed property for display description (truncated if needed)
    var displayDescription: String {
        if description.count > 100 {
            return String(description.prefix(100)) + "..."
        }
        return description
    }
}

// MARK: - Mock Data for Preview
extension Course {
    static let mockCourses: [Course] = [
        Course(
            id: 1,
            name: "Curso de React",
            description: "Aprende React desde cero hasta convertirte en un experto. Domina componentes, hooks, estado y mucho más en este curso completo.",
            thumbnail: "https://via.placeholder.com/300x200/007AFF/FFFFFF?text=React",
            slug: "curso-de-react",
            teacherIds: [1, 2],
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        ),
        Course(
            id: 2,
            name: "Curso de Swift",
            description: "Desarrolla aplicaciones iOS con Swift y SwiftUI. Aprende desde los fundamentos hasta crear apps profesionales.",
            thumbnail: "https://via.placeholder.com/300x200/34C759/FFFFFF?text=Swift",
            slug: "curso-de-swift",
            teacherIds: [2],
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        ),
        Course(
            id: 3,
            name: "Curso de JavaScript",
            description: "Domina JavaScript moderno con ES6+, async/await, promises y las mejores prácticas de desarrollo.",
            thumbnail: "https://via.placeholder.com/300x200/FF9500/FFFFFF?text=JavaScript",
            slug: "curso-de-javascript",
            teacherIds: [1, 3],
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        )
    ]
} 