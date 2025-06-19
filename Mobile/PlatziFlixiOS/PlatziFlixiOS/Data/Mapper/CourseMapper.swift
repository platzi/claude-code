//
//  CourseMapper.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Mapper to convert DTOs to Domain Models
struct CourseMapper {
    
    /// Converts CourseDTO to Course domain model
    static func toDomain(_ dto: CourseDTO) -> Course {
        return Course(
            id: dto.id,
            name: dto.name,
            description: dto.description,
            thumbnail: dto.thumbnail,
            slug: dto.slug,
            teacherIds: dto.teacherId ?? [],
            createdAt: parseDate(dto.createdAt),
            updatedAt: parseDate(dto.updatedAt),
            deletedAt: parseDate(dto.deletedAt)
        )
    }
    
    /// Converts array of CourseDTOs to array of Course domain models
    static func toDomain(_ dtos: [CourseDTO]) -> [Course] {
        return dtos.map { toDomain($0) }
    }
    
    /// Converts CourseDetailDTO to Course domain model
    static func toDomain(_ dto: CourseDetailDTO) -> Course {
        return Course(
            id: dto.id,
            name: dto.name,
            description: dto.description,
            thumbnail: dto.thumbnail,
            slug: dto.slug,
            teacherIds: dto.teacherId ?? [],
            createdAt: nil, // Detail DTO doesn't include dates
            updatedAt: nil,
            deletedAt: nil
        )
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
