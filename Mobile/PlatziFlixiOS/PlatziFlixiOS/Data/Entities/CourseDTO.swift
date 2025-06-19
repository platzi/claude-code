//
//  CourseDTO.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Data Transfer Object for Course from API
struct CourseDTO: Codable {
    let id: Int
    let name: String
    let description: String
    let thumbnail: String
    let slug: String
    let createdAt: String?
    let updatedAt: String?
    let deletedAt: String?
    let teacherId: [Int]?
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case thumbnail
        case slug
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case deletedAt = "deleted_at"
        case teacherId = "teacher_id"
    }
}

/// CourseDTO for detailed course response (with classes)
struct CourseDetailDTO: Codable {
    let id: Int
    let name: String
    let description: String
    let thumbnail: String
    let slug: String
    let teacherId: [Int]?
    let classes: [ClassDTO]?
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case thumbnail
        case slug
        case teacherId = "teacher_id"
        case classes
    }
}

/// Class DTO for course classes
struct ClassDTO: Codable {
    let id: Int
    let name: String
    let description: String
    let slug: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case slug
    }
}
