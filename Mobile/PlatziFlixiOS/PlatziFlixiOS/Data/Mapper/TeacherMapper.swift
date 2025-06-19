//
//  TeacherMapper.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Mapper to convert Teacher DTOs to Domain Models
struct TeacherMapper {
    
    /// Converts TeacherDTO to Teacher domain model
    static func toDomain(_ dto: TeacherDTO) -> Teacher {
        return Teacher(
            id: dto.id,
            name: dto.name,
            email: dto.email,
            createdAt: parseDate(dto.createdAt),
            updatedAt: parseDate(dto.updatedAt),
            deletedAt: parseDate(dto.deletedAt)
        )
    }
    
    /// Converts array of TeacherDTOs to array of Teacher domain models
    static func toDomain(_ dtos: [TeacherDTO]) -> [Teacher] {
        return dtos.map { toDomain($0) }
    }
    
    // MARK: - Private Helpers
    
    /// Parses ISO8601 date string to Date
    private static func parseDate(_ dateString: String?) -> Date? {
        guard let dateString = dateString else { return nil }
        
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        if let date = formatter.date(from: dateString) {
            return date
        }
        
        // Fallback to simple date format
        let simpleDateFormatter = DateFormatter()
        simpleDateFormatter.dateFormat = "yyyy-MM-dd"
        return simpleDateFormatter.date(from: dateString)
    }
} 