//
//  CourseAPIEndpoints.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// API Endpoints for Course operations
enum CourseAPIEndpoints {
    case getAllCourses
    case getCourseBySlug(String)
}

extension CourseAPIEndpoints: APIEndpoint {
    var baseURL: String {
        return "http://localhost:8000"
    }
    
    var path: String {
        switch self {
        case .getAllCourses:
            return "/courses"
        case .getCourseBySlug(let slug):
            return "/courses/\(slug)"
        }
    }
    
    var method: HTTPMethod {
        switch self {
        case .getAllCourses, .getCourseBySlug:
            return .GET
        }
    }
    
    var headers: [String : String]? {
        return nil // Using default headers from APIEndpoint extension
    }
    
    var parameters: [String : Any]? {
        return nil
    }
    
    var body: Data? {
        return nil
    }
} 