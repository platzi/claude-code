//
//  CourseRepositoryProtocol.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Protocol defining the contract for course data operations
protocol CourseRepository {
    
    /// Fetches all courses from the data source
    /// - Returns: Array of courses or throws an error
    func getAllCourses() async throws -> [Course]
    
    /// Fetches a specific course by its slug
    /// - Parameter slug: The unique identifier for the course
    /// - Returns: Course details or throws an error
    func getCourseBySlug(_ slug: String) async throws -> Course
    
    /// Fetches all courses with Result wrapper
    /// - Returns: Result containing array of courses or error
    func getAllCoursesResult() async -> Result<[Course], Error>
    
    /// Fetches a specific course by its slug with Result wrapper
    /// - Parameter slug: The unique identifier for the course
    /// - Returns: Result containing course details or error
    func getCourseBySlugResult(_ slug: String) async -> Result<Course, Error>
}
