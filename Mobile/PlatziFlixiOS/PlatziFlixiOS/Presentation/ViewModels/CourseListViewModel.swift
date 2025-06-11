import Foundation
import Combine

/// ViewModel responsible for managing the course list state and business logic
@MainActor
class CourseListViewModel: ObservableObject {
    
    // MARK: - Published Properties
    @Published var courses: [Course] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String? = nil
    @Published var searchText: String = ""
    
    // MARK: - Computed Properties
    
    /// Filtered courses based on search text
    var filteredCourses: [Course] {
        if searchText.isEmpty {
            return courses
        }
        return courses.filter { course in
            course.name.localizedCaseInsensitiveContains(searchText) ||
            course.description.localizedCaseInsensitiveContains(searchText)
        }
    }
    
    /// Whether there are no courses to display
    var isEmpty: Bool {
        filteredCourses.isEmpty && !isLoading
    }
    
    /// Loading state for UI feedback
    var isLoadingCourses: Bool {
        isLoading && courses.isEmpty
    }
    
    // MARK: - Private Properties
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    init() {
        setupBindings()
        loadCourses()
    }
    
    // MARK: - Public Methods
    
    /// Loads the courses from the repository
    func loadCourses() {
        isLoading = true
        errorMessage = nil
        
        // Simulate API call delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            guard let self = self else { return }
            
            // Using mock data for now - this would be replaced with repository call
            self.courses = Course.mockCourses
            self.isLoading = false
        }
    }
    
    /// Refreshes the course list
    func refreshCourses() {
        loadCourses()
    }
    
    /// Handles course selection
    func selectCourse(_ course: Course) {
        // TODO: Navigate to course detail
        print("Selected course: \(course.name)")
    }
    
    /// Clears error message
    func clearError() {
        errorMessage = nil
    }
    
    // MARK: - Private Methods
    
    private func setupBindings() {
        // Debounce search text changes for better performance
        $searchText
            .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
            .sink { _ in
                // Search filtering is handled by computed property
            }
            .store(in: &cancellables)
    }
} 