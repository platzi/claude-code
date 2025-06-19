package com.espaciotiago.platziflixandroid.presentation.courses.screen

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LargeTopAppBar
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.tooling.preview.Preview
import com.espaciotiago.platziflixandroid.domain.models.Course
import com.espaciotiago.platziflixandroid.presentation.courses.components.CourseCard
import com.espaciotiago.platziflixandroid.presentation.courses.components.ErrorMessage
import com.espaciotiago.platziflixandroid.presentation.courses.components.LoadingIndicator
import com.espaciotiago.platziflixandroid.presentation.courses.state.CourseListUiEvent
import com.espaciotiago.platziflixandroid.presentation.courses.state.CourseListUiState
import com.espaciotiago.platziflixandroid.presentation.courses.viewmodel.CourseListViewModel
import com.espaciotiago.platziflixandroid.ui.theme.PlatziFlixAndroidTheme
import com.espaciotiago.platziflixandroid.ui.theme.Spacing

/**
 * Screen that displays a list of courses
 * 
 * @param viewModel ViewModel to handle business logic
 * @param onCourseClick Callback when a course is clicked
 * @param modifier Modifier for styling
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CourseListScreen(
    viewModel: CourseListViewModel,
    onCourseClick: (Course) -> Unit,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    val scrollBehavior = TopAppBarDefaults.exitUntilCollapsedScrollBehavior()
    
    Scaffold(
        modifier = modifier.nestedScroll(scrollBehavior.nestedScrollConnection),
        topBar = {
            LargeTopAppBar(
                title = {
                    Text(
                        text = "Cursos",
                        style = MaterialTheme.typography.headlineMedium
                    )
                },
                actions = {
                    IconButton(
                        onClick = { 
                            viewModel.handleEvent(CourseListUiEvent.RefreshCourses)
                        }
                    ) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Actualizar cursos"
                        )
                    }
                },
                scrollBehavior = scrollBehavior
            )
        }
    ) { innerPadding ->
        CourseListContent(
            uiState = uiState,
            onCourseClick = onCourseClick,
            onRetry = { viewModel.handleEvent(CourseListUiEvent.LoadCourses) },
            modifier = Modifier.padding(innerPadding)
        )
    }
}

/**
 * Content of the course list based on UI state
 */
@Composable
private fun CourseListContent(
    uiState: CourseListUiState,
    onCourseClick: (Course) -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    when {
        uiState.isLoading && uiState.courses.isEmpty() -> {
            LoadingIndicator(
                modifier = modifier.fillMaxSize()
            )
        }
        
        uiState.error != null && uiState.courses.isEmpty() -> {
            Box(
                modifier = modifier
                    .fillMaxSize()
                    .padding(Spacing.medium),
                contentAlignment = Alignment.Center
            ) {
                ErrorMessage(
                    message = uiState.error,
                    onRetry = onRetry
                )
            }
        }
        
        uiState.courses.isEmpty() -> {
            Box(
                modifier = modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "No hay cursos disponibles",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        
        else -> {
            LazyColumn(
                modifier = modifier.fillMaxSize(),
                contentPadding = PaddingValues(Spacing.medium),
                verticalArrangement = Arrangement.spacedBy(Spacing.medium)
            ) {
                // Show error message at top if there's an error but we have courses
                uiState.error?.let { error ->
                    item {
                        ErrorMessage(
                            message = error,
                            onRetry = onRetry,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
                
                items(
                    items = uiState.courses,
                    key = { course -> course.id }
                ) { course ->
                    CourseCard(
                        course = course,
                        onClick = onCourseClick
                    )
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun CourseListScreenPreview() {
    PlatziFlixAndroidTheme {
        CourseListContent(
            uiState = CourseListUiState(
                courses = listOf(
                    Course(
                        id = 1,
                        name = "Curso de Kotlin",
                        description = "Aprende Kotlin desde cero hasta convertirte en un desarrollador experto",
                        thumbnail = "https://via.placeholder.com/300x200",
                        slug = "curso-de-kotlin"
                    ),
                    Course(
                        id = 2,
                        name = "Curso de Android",
                        description = "Desarrolla aplicaciones móviles nativas para Android usando las mejores prácticas",
                        thumbnail = "https://via.placeholder.com/300x200",
                        slug = "curso-de-android"
                    )
                )
            ),
            onCourseClick = { },
            onRetry = { }
        )
    }
} 