package com.espaciotiago.platziflixandroid.data.mappers

import com.espaciotiago.platziflixandroid.data.entities.CourseDTO
import com.espaciotiago.platziflixandroid.domain.models.Course

/**
 * Mapper to convert between CourseDTO and Course domain model
 */
object CourseMapper {
    
    /**
     * Converts CourseDTO to Course domain model
     */
    fun fromDTO(courseDTO: CourseDTO): Course {
        return Course(
            id = courseDTO.id,
            name = courseDTO.name,
            description = courseDTO.description,
            thumbnail = courseDTO.thumbnail,
            slug = courseDTO.slug
        )
    }
    
    /**
     * Converts list of CourseDTO to list of Course domain models
     */
    fun fromDTOList(courseDTOList: List<CourseDTO>): List<Course> {
        return courseDTOList.map { fromDTO(it) }
    }
} 