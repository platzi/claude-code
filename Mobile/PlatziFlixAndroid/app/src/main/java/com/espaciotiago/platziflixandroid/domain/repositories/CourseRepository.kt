package com.espaciotiago.platziflixandroid.domain.repositories

import com.espaciotiago.platziflixandroid.domain.models.Course

/**
 * Repository interface for Course operations
 */
interface CourseRepository {
    
    /**
     * Retrieves all courses from the data source
     * @return Result containing list of courses or error
     */
    suspend fun getAllCourses(): Result<List<Course>>
} 