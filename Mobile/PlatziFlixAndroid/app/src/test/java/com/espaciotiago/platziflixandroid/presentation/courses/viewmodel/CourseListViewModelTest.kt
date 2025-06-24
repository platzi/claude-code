package com.espaciotiago.platziflixandroid.presentation.courses.viewmodel

import com.espaciotiago.platziflixandroid.domain.models.Course
import com.espaciotiago.platziflixandroid.domain.repositories.CourseRepository
import com.espaciotiago.platziflixandroid.presentation.courses.state.CourseListUiEvent
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class CourseListViewModelTest {
    
    private val testDispatcher = StandardTestDispatcher()
    private lateinit var mockRepository: MockCourseRepository
    private lateinit var viewModel: CourseListViewModel
    
    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        mockRepository = MockCourseRepository()
        viewModel = CourseListViewModel(mockRepository)
    }
    
    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }
    
    @Test
    fun `initial state should be loading`() = runTest {
        val initialState = viewModel.uiState.first()
        
        assertTrue("Should be loading initially", initialState.isLoading)
        assertTrue("Courses should be empty initially", initialState.courses.isEmpty())
        assertNull("Error should be null initially", initialState.error)
        assertFalse("Should not be refreshing initially", initialState.isRefreshing)
    }
    
    @Test
    fun `loadCourses should update state with courses on success`() = runTest {
        // Given
        val expectedCourses = mockRepository.getMockCourses()
        
        // When
        viewModel.handleEvent(CourseListUiEvent.LoadCourses)
        testDispatcher.scheduler.advanceUntilIdle()
        
        // Then
        val finalState = viewModel.uiState.first()
        assertFalse("Should not be loading after success", finalState.isLoading)
        assertEquals("Should have expected courses", expectedCourses.size, finalState.courses.size)
        assertNull("Error should be null on success", finalState.error)
    }
    
    @Test
    fun `loadCourses should update state with error on failure`() = runTest {
        // Given
        val failingRepository = FailingCourseRepository()
        val failingViewModel = CourseListViewModel(failingRepository)
        
        // When
        failingViewModel.handleEvent(CourseListUiEvent.LoadCourses)
        testDispatcher.scheduler.advanceUntilIdle()
        
        // Then
        val finalState = failingViewModel.uiState.first()
        assertFalse("Should not be loading after failure", finalState.isLoading)
        assertTrue("Courses should be empty on failure", finalState.courses.isEmpty())
        assertEquals("Should have error message", "Test error", finalState.error)
    }
    
    @Test
    fun `refreshCourses should set refreshing state`() = runTest {
        // When
        viewModel.handleEvent(CourseListUiEvent.RefreshCourses)
        
        // Then
        val refreshingState = viewModel.uiState.first()
        assertTrue("Should be refreshing", refreshingState.isRefreshing)
        assertNull("Error should be cleared during refresh", refreshingState.error)
    }
    
    @Test
    fun `clearError should remove error from state`() = runTest {
        // Given - simulate an error state
        val failingRepository = FailingCourseRepository()
        val failingViewModel = CourseListViewModel(failingRepository)
        failingViewModel.handleEvent(CourseListUiEvent.LoadCourses)
        testDispatcher.scheduler.advanceUntilIdle()
        
        // When
        failingViewModel.handleEvent(CourseListUiEvent.ClearError)
        
        // Then
        val finalState = failingViewModel.uiState.first()
        assertNull("Error should be cleared", finalState.error)
    }
    
    // Mock repository that returns test data
    private class MockCourseRepository : CourseRepository {
        fun getMockCourses() = listOf(
            Course(1, "Test Course 1", "Description 1", "thumb1.jpg", "test-1"),
            Course(2, "Test Course 2", "Description 2", "thumb2.jpg", "test-2")
        )
        
        override suspend fun getAllCourses(): Result<List<Course>> {
            return Result.success(getMockCourses())
        }
    }
    
    // Mock repository that always fails
    private class FailingCourseRepository : CourseRepository {
        override suspend fun getAllCourses(): Result<List<Course>> {
            return Result.failure(Exception("Test error"))
        }
    }
} 