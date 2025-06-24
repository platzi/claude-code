//
//  RemoteCourseRepository.swift
//  PlatziFlixiOS
//
//  Created by Santiago Moreno on 11/06/25.
//

import Foundation

/// Remote implementation of CourseRepository
/// Fetches course data from the API using NetworkService
final class RemoteCourseRepository: CourseRepository {
    
    // MARK: - Properties
    private let networkService: NetworkService
    
    // MARK: - Initialization
    init(networkService: NetworkService = NetworkManager.shared) {
        self.networkService = networkService
    }
    
    // MARK: - CourseRepository Implementation
    
    /// Fetches all courses from the remote API
    func getAllCourses() async throws -> [Course] {
        let endpoint = CourseAPIEndpoints.getAllCourses
        let courseDTOs = try await networkService.request(endpoint, responseType: [CourseDTO].self)
        return CourseMapper.toDomain(courseDTOs)
    }
    
    /// Fetches a specific course by slug from the remote API
    func getCourseBySlug(_ slug: String) async throws -> Course {
        let endpoint = CourseAPIEndpoints.getCourseBySlug(slug)
        let courseDetailDTO = try await networkService.request(endpoint, responseType: CourseDetailDTO.self)
        return CourseMapper.toDomain(courseDetailDTO)
    }
    
    /// Fetches all courses with Result wrapper for error handling
    func getAllCoursesResult() async -> Result<[Course], Error> {
        do {
            let courses = try await getAllCourses()
            return .success(courses)
        } catch {
            return .failure(error)
        }
    }
    
    /// Fetches a specific course by slug with Result wrapper for error handling
    func getCourseBySlugResult(_ slug: String) async -> Result<Course, Error> {
        do {
            let course = try await getCourseBySlug(slug)
            return .success(course)
        } catch {
            return .failure(error)
        }
    }
}
