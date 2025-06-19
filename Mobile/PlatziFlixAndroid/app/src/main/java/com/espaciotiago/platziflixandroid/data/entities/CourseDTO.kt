package com.espaciotiago.platziflixandroid.data.entities

import com.google.gson.annotations.SerializedName

/**
 * Data Transfer Object for Course entity from API
 */
data class CourseDTO(
    @SerializedName("id")
    val id: Int,
    
    @SerializedName("name")
    val name: String,
    
    @SerializedName("description")
    val description: String,
    
    @SerializedName("thumbnail")
    val thumbnail: String,
    
    @SerializedName("slug")
    val slug: String,
    
    @SerializedName("created_at")
    val createdAt: String? = null,
    
    @SerializedName("updated_at")
    val updatedAt: String? = null,
    
    @SerializedName("deleted_at")
    val deletedAt: String? = null,
    
    @SerializedName("teacher_id")
    val teacherIds: List<Int>? = null
) 