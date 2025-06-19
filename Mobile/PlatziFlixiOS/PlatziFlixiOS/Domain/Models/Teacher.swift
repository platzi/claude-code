//
//  Teacher.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Domain model representing a teacher in Platziflix
struct Teacher: Identifiable, Equatable {
    let id: Int
    let name: String
    let email: String
    let createdAt: Date?
    let updatedAt: Date?
    let deletedAt: Date?
    
    /// Computed property to check if teacher is active
    var isActive: Bool {
        deletedAt == nil
    }
    
    /// Computed property for display name with initials
    var displayName: String {
        return name
    }
    
    /// Computed property to get initials from name
    var initials: String {
        let components = name.components(separatedBy: " ")
        let initials = components.compactMap { $0.first }
        return String(initials.prefix(2)).uppercased()
    }
}

// MARK: - Mock Data for Preview
extension Teacher {
    static let mockTeachers: [Teacher] = [
        Teacher(
            id: 1,
            name: "Ana García",
            email: "ana.garcia@platzi.com",
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        ),
        Teacher(
            id: 2,
            name: "Carlos Mendoza",
            email: "carlos.mendoza@platzi.com",
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        ),
        Teacher(
            id: 3,
            name: "Laura Rodríguez",
            email: "laura.rodriguez@platzi.com",
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        ),
        Teacher(
            id: 4,
            name: "Diego Fernández",
            email: "diego.fernandez@platzi.com",
            createdAt: Date(),
            updatedAt: Date(),
            deletedAt: nil
        )
    ]
} 