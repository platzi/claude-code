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
                        .fill(Color.neutralGray200)
                        .aspectRatio(16/9, contentMode: .fit)
                        .overlay(
                            Image(systemName: "photo")
                                .font(.title2)
                                .foregroundColor(Color.neutralGray600)
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
                        .foregroundColor(.neutralBlack)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                        .accessibilityAddTraits(.isHeader)
                    
                    Text(course.displayDescription)
                        .font(.bodyRegular)
                        .foregroundColor(.neutralGray600)
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

// MARK: - Preview
struct CourseCardView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            // Light mode preview
            CourseCardView(course: Course.mockCourses[0]) {
                print("Course tapped")
            }
            .padding()
            .previewDisplayName("Light Mode")
            
            // Dark mode preview
            CourseCardView(course: Course.mockCourses[1]) {
                print("Course tapped")
            }
            .padding()
            .preferredColorScheme(.dark)
            .previewDisplayName("Dark Mode")
            
            // Grid preview
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: Spacing.spacing4) {
                ForEach(Course.mockCourses.prefix(4), id: \.id) { course in
                    CourseCardView(course: course)
                }
            }
            .padding()
            .previewDisplayName("Grid Layout")
        }
    }
} 