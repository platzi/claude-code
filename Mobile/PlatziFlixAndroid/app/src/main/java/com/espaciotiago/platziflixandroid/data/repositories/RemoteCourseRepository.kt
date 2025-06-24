package com.espaciotiago.platziflixandroid.data.repositories

import com.espaciotiago.platziflixandroid.data.mappers.CourseMapper
import com.espaciotiago.platziflixandroid.data.network.ApiService
import com.espaciotiago.platziflixandroid.domain.models.Course
import com.espaciotiago.platziflixandroid.domain.repositories.CourseRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Implementation of CourseRepository that fetches data from remote API
 */
class RemoteCourseRepository(
    private val apiService: ApiService
) : CourseRepository {
    
    /**
     * Retrieves all courses from the remote API
     * @return Result containing list of courses or error
     */
    override suspend fun getAllCourses(): Result<List<Course>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getAllCourses()
                if (response.isSuccessful) {
                    val courseDTOList = response.body() ?: emptyList()
                    val courseList = CourseMapper.fromDTOList(courseDTOList)
                    Result.success(courseList)
                } else {
                    Result.failure(
                        Exception("Failed to fetch courses: ${response.code()} ${response.message()}")
                    )
                }
            } catch (exception: Exception) {
                Result.failure(exception)
            }
        }
    }
} 