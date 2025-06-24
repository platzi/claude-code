package com.espaciotiago.platziflixandroid.data.network

import com.espaciotiago.platziflixandroid.data.entities.CourseDTO
import retrofit2.Response
import retrofit2.http.GET

/**
 * API service interface for course-related endpoints
 */
interface ApiService {
    
    /**
     * Fetches all courses from the API
     * @return Response containing list of courses
     */
    @GET("courses")
    suspend fun getAllCourses(): Response<List<CourseDTO>>
} 