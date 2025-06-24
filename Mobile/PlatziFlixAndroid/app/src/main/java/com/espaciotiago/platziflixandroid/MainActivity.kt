package com.espaciotiago.platziflixandroid

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.lifecycle.viewmodel.compose.viewModel
import com.espaciotiago.platziflixandroid.di.AppModule
import com.espaciotiago.platziflixandroid.domain.models.Course
import com.espaciotiago.platziflixandroid.presentation.courses.screen.CourseListScreen
import com.espaciotiago.platziflixandroid.presentation.courses.viewmodel.CourseListViewModel
import com.espaciotiago.platziflixandroid.ui.theme.PlatziFlixAndroidTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PlatziFlixAndroidTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    PlatziFlixApp()
                }
            }
        }
    }
}

@Composable
fun PlatziFlixApp() {
    val courseListViewModel = viewModel<CourseListViewModel> {
        AppModule.provideCourseListViewModel()
    }
    
    CourseListScreen(
        viewModel = courseListViewModel,
        onCourseClick = { course ->
            // TODO: Navigate to course detail screen
        }
    )
}

@Preview(showBackground = true)
@Composable
fun PlatziFlixAppPreview() {
    PlatziFlixAndroidTheme {
        // Preview with mock data would go here
    }
}