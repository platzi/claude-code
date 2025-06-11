package com.espaciotiago.platziflixandroid.domain.models

/**
 * Domain model representing a Course
 */
data class Course(
    val id: Int,
    val name: String,
    val description: String,
    val thumbnail: String,
    val slug: String
) 