//
//  ClassDetailDTO.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Data Transfer Object for detailed Class information from API
struct ClassDetailDTO: Codable {
    let id: Int
    let courseId: Int
    let name: String
    let description: String
    let slug: String
    let videoUrl: String
    let createdAt: String?
    let updatedAt: String?
    let deletedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case courseId = "course_id"
        case name
        case description
        case slug
        case videoUrl = "video_url"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case deletedAt = "deleted_at"
    }
} 