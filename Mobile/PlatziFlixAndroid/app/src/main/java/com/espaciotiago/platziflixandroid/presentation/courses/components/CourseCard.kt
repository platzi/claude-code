package com.espaciotiago.platziflixandroid.presentation.courses.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.espaciotiago.platziflixandroid.R
import com.espaciotiago.platziflixandroid.domain.models.Course
import com.espaciotiago.platziflixandroid.ui.theme.CornerRadius
import com.espaciotiago.platziflixandroid.ui.theme.PlatziFlixAndroidTheme
import com.espaciotiago.platziflixandroid.ui.theme.Spacing

/**
 * Card component that displays course information
 * 
 * @param course The course data to display
 * @param onClick Callback when the card is clicked
 * @param modifier Modifier for styling
 */
@Composable
fun CourseCard(
    course: Course,
    onClick: (Course) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = { onClick(course) },
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(CornerRadius.large),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = Spacing.extraSmall
        )
    ) {
        Column(
            modifier = Modifier.fillMaxWidth()
        ) {
            // Course thumbnail
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(16f / 9f)
                    .clip(RoundedCornerShape(
                        topStart = CornerRadius.large,
                        topEnd = CornerRadius.large
                    ))
            ) {
                AsyncImage(
                    model = ImageRequest.Builder(LocalContext.current)
                        .data(course.thumbnail)
                        .crossfade(true)
                        .build(),
                    contentDescription = "Thumbnail for ${course.name}",
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop,
                    placeholder = painterResource(id = android.R.drawable.ic_menu_gallery),
                    error = painterResource(id = android.R.drawable.ic_menu_gallery)
                )
                
                // Placeholder for image loading state
                if (course.thumbnail.isEmpty()) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .clip(RoundedCornerShape(
                                topStart = CornerRadius.large,
                                topEnd = CornerRadius.large
                            )),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Sin imagen",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            
            // Course content
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(Spacing.medium),
                verticalArrangement = Arrangement.spacedBy(Spacing.small)
            ) {
                // Course name
                Text(
                    text = course.name,
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                
                // Course description
                Text(
                    text = course.description,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 3,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Preview(showBackground = true, uiMode = android.content.res.Configuration.UI_MODE_NIGHT_YES)
@Composable
fun CourseCardPreview() {
    PlatziFlixAndroidTheme {
        CourseCard(
            course = Course(
                id = 1,
                name = "Curso de Kotlin",
                description = "Aprende Kotlin desde cero hasta convertirte en un desarrollador experto",
                thumbnail = "https://via.placeholder.com/300x200",
                slug = "curso-de-kotlin"
            ),
            onClick = { }
        )
    }
} 