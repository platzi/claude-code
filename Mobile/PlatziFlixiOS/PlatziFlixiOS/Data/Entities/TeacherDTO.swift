//
//  TeacherDTO.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Data Transfer Object for Teacher from API
struct TeacherDTO: Codable {
    let id: Int
    let name: String
    let email: String
    let createdAt: String?
    let updatedAt: String?
    let deletedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case email
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case deletedAt = "deleted_at"
    }
} 