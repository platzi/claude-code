//
//  ClassMapper.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Mapper to convert Class DTOs to Domain Models
struct ClassMapper {
    
    /// Converts ClassDetailDTO to Class domain model
    static func toDomain(_ dto: ClassDetailDTO) -> Class {
        return Class(
            id: dto.id,
            courseId: dto.courseId,
            name: dto.name,
            description: dto.description,
            slug: dto.slug,
            videoUrl: dto.videoUrl,
            createdAt: parseDate(dto.createdAt),
            updatedAt: parseDate(dto.updatedAt),
            deletedAt: parseDate(dto.deletedAt)
        )
    }
    
    /// Converts ClassDTO to Class domain model (for basic class info)
    static func toDomain(_ dto: ClassDTO) -> Class {
        return Class(
            id: dto.id,
            courseId: 0, // Not available in basic ClassDTO
            name: dto.name,
            description: dto.description,
            slug: dto.slug,
            videoUrl: nil, // Not available in basic ClassDTO
            createdAt: nil,
            updatedAt: nil,
            deletedAt: nil
        )
    }
    
    /// Converts array of ClassDetailDTOs to array of Class domain models
    static func toDomain(_ dtos: [ClassDetailDTO]) -> [Class] {
        return dtos.map { toDomain($0) }
    }
    
    /// Converts array of ClassDTOs to array of Class domain models
    static func toDomainFromBasicDTO(_ dtos: [ClassDTO]) -> [Class] {
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