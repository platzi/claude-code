package com.espaciotiago.platziflixandroid.data.repositories

import com.espaciotiago.platziflixandroid.domain.models.Course
import com.espaciotiago.platziflixandroid.domain.repositories.CourseRepository
import kotlinx.coroutines.delay

/**
 * Mock implementation of CourseRepository for testing and development
 */
class MockCourseRepository : CourseRepository {
    
    private val mockCourses = listOf(
        Course(
            id = 1,
            name = "Curso de Kotlin",
            description = "Aprende Kotlin desde cero hasta convertirte en un desarrollador experto. Cubre desde conceptos básicos hasta programación avanzada.",
            thumbnail = "https://static.platzi.com/media/achievements/badge-kotlin-2021.png",
            slug = "curso-de-kotlin"
        ),
        Course(
            id = 2,
            name = "Curso de Android con Jetpack Compose",
            description = "Desarrolla aplicaciones móviles modernas usando Jetpack Compose y las mejores prácticas de Android.",
            thumbnail = "https://static.platzi.com/media/achievements/badge-jetpack-compose-d4e5d00f-b4b0-4fc8-be33-3d7b3e966da3.png",
            slug = "curso-android-jetpack-compose"
        ),
        Course(
            id = 3,
            name = "Curso de Clean Architecture",
            description = "Implementa arquitectura limpia en tus proyectos Android para código mantenible y escalable.",
            thumbnail = "https://static.platzi.com/media/achievements/badge-clean-architecture-android.png",
            slug = "curso-clean-architecture"
        ),
        Course(
            id = 4,
            name = "Curso de Testing en Android",
            description = "Aprende a crear pruebas unitarias e instrumentadas para garantizar la calidad de tus aplicaciones.",
            thumbnail = "https://static.platzi.com/media/achievements/badge-testing-android.png",
            slug = "curso-testing-android"
        ),
        Course(
            id = 5,
            name = "Curso de Material Design 3",
            description = "Diseña interfaces hermosas y funcionales siguiendo las directrices de Material Design 3.",
            thumbnail = "https://static.platzi.com/media/achievements/badge-material-design.png",
            slug = "curso-material-design-3"
        )
    )
    
    override suspend fun getAllCourses(): Result<List<Course>> {
        // Simulate network delay
        delay(1500)
        
        // Simulate occasional failures for testing error states
        if (Math.random() < 0.1) { // 10% chance of failure
            return Result.failure(Exception("Error de conexión: No se pudo conectar al servidor"))
        }
        
        return Result.success(mockCourses)
    }
} 