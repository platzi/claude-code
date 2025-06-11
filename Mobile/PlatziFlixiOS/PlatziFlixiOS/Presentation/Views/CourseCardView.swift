import SwiftUI
import Foundation

/// Course card component that displays a course with its thumbnail and information
struct CourseCardView: View {
    let course: Course
    let onTap: (() -> Void)?
    
    init(course: Course, onTap: (() -> Void)? = nil) {
        self.course = course
        self.onTap = onTap
    }
    
    var body: some View {
        Button(action: {
            onTap?()
        }) {
            VStack(alignment: .leading, spacing: Spacing.spacing3) {
                // Course thumbnail
                AsyncImage(url: URL(string: course.thumbnail)) { image in
                    image
                        .resizable()
                        .aspectRatio(16/9, contentMode: .fill)
                } placeholder: {
                    RoundedRectangle(cornerRadius: Radius.radiusMedium)
                        .fill(Color(.systemGray5))
                        .aspectRatio(16/9, contentMode: .fit)
                        .overlay(
                            Image(systemName: "photo")
                                .font(.title2)
                                .foregroundColor(.secondary)
                        )
                }
                .frame(height: 160)
                .clipped()
                .cornerRadius(Radius.radiusMedium)
                .accessibilityLabel("Imagen del curso \(course.name)")
                
                // Course information
                VStack(alignment: .leading, spacing: Spacing.spacing2) {
                    Text(course.name)
                        .font(.title3)
                        .foregroundColor(.primary)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                        .accessibilityAddTraits(.isHeader)
                    
                    Text(course.displayDescription)
                        .font(.bodyRegular)
                        .foregroundColor(.secondary)
                        .lineLimit(3)
                        .multilineTextAlignment(.leading)
                }
                .padding(.horizontal, Spacing.spacing3)
                .padding(.bottom, Spacing.spacing4)
            }
        }
        .buttonStyle(PlainButtonStyle())
        .cardStyle()
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Curso: \(course.name)")
        .accessibilityHint("Doble toque para ver los detalles del curso")
        .accessibilityAction(named: "Ver curso") {
            onTap?()
        }
    }
}

// MARK: - Previews
#Preview("Light Mode") {
    CourseCardView(course: Course.mockCourses[0]) {
        print("Course tapped")
    }
    .padding()
}

#Preview("Dark Mode") {
    CourseCardView(course: Course.mockCourses[1]) {
        print("Course tapped")
    }
    .padding()
    .preferredColorScheme(.dark)
}

#Preview("Grid Layout") {
    LazyVGrid(columns: [
        GridItem(.flexible()),
        GridItem(.flexible())
    ], spacing: Spacing.spacing4) {
        ForEach(Course.mockCourses.prefix(4), id: \.id) { course in
            CourseCardView(course: course)
        }
    }
    .padding()
} 