package com.espaciotiago.platziflixandroid.presentation.courses.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.espaciotiago.platziflixandroid.domain.repositories.CourseRepository
import com.espaciotiago.platziflixandroid.presentation.courses.state.CourseListUiEvent
import com.espaciotiago.platziflixandroid.presentation.courses.state.CourseListUiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for Course List screen following MVI pattern
 */
class CourseListViewModel(
    private val courseRepository: CourseRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(CourseListUiState())
    val uiState: StateFlow<CourseListUiState> = _uiState.asStateFlow()
    
    init {
        loadCourses()
    }
    
    /**
     * Handles UI events from the View
     */
    fun handleEvent(event: CourseListUiEvent) {
        when (event) {
            is CourseListUiEvent.LoadCourses -> loadCourses()
            is CourseListUiEvent.RefreshCourses -> refreshCourses()
            is CourseListUiEvent.ClearError -> clearError()
        }
    }
    
    /**
     * Loads courses from repository
     */
    private fun loadCourses() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                error = null
            )
            
            courseRepository.getAllCourses()
                .onSuccess { courses ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        courses = courses,
                        error = null
                    )
                }
                .onFailure { exception ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = exception.message ?: "Unknown error occurred"
                    )
                }
        }
    }
    
    /**
     * Refreshes courses list
     */
    private fun refreshCourses() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isRefreshing = true,
                error = null
            )
            
            courseRepository.getAllCourses()
                .onSuccess { courses ->
                    _uiState.value = _uiState.value.copy(
                        isRefreshing = false,
                        courses = courses,
                        error = null
                    )
                }
                .onFailure { exception ->
                    _uiState.value = _uiState.value.copy(
                        isRefreshing = false,
                        error = exception.message ?: "Unknown error occurred"
                    )
                }
        }
    }
    
    /**
     * Clears error state
     */
    private fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
} 