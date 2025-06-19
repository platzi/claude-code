package com.espaciotiago.platziflixandroid.presentation.courses.state

import com.espaciotiago.platziflixandroid.domain.models.Course

/**
 * UI State for the Course List screen
 */
data class CourseListUiState(
    val isLoading: Boolean = false,
    val courses: List<Course> = emptyList(),
    val error: String? = null,
    val isRefreshing: Boolean = false
)

/**
 * UI Events for the Course List screen
 */
sealed class CourseListUiEvent {
    object LoadCourses : CourseListUiEvent()
    object RefreshCourses : CourseListUiEvent()
    object ClearError : CourseListUiEvent()
} 