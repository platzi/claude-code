import SwiftUI

/// Main view that displays the list of courses
struct CourseListView: View {
    @StateObject private var viewModel = CourseListViewModel()
    @State private var showSearchBar = false
    
    // Grid configuration for course cards
    private let columns = [
        GridItem(.flexible(), spacing: Spacing.spacing4),
        GridItem(.flexible(), spacing: Spacing.spacing4)
    ]
    
    var body: some View {
        NavigationView {
            ZStack {
                // Background color
                Color.neutralGray200
                    .ignoresSafeArea()
                
                if viewModel.isLoadingCourses {
                    // Loading state
                    loadingView
                } else if viewModel.isEmpty {
                    // Empty state
                    emptyView
                } else {
                    // Course list content
                    courseListContent
                }
            }
            .navigationTitle("Últimos cursos lanzados")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        withAnimation(.easeInOut(duration: 0.3)) {
                            showSearchBar.toggle()
                        }
                    }) {
                        Image(systemName: "magnifyingglass")
                            .foregroundColor(.primaryBlue)
                    }
                    .accessibilityLabel("Buscar cursos")
                }
            }
            .searchable(
                text: $viewModel.searchText,
                isPresented: $showSearchBar,
                placement: .navigationBarDrawer(displayMode: .always),
                prompt: "Buscar cursos..."
            )
            .refreshable {
                await MainActor.run {
                    viewModel.refreshCourses()
                }
            }
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
    
    // MARK: - View Components
    
    private var loadingView: some View {
        VStack(spacing: Spacing.spacing6) {
            ProgressView()
                .scaleEffect(1.5)
                .progressViewStyle(CircularProgressViewStyle(tint: .primaryBlue))
            
            Text("Cargando cursos...")
                .font(.bodyEmphasized)
                .foregroundColor(.neutralGray600)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Cargando cursos")
    }
    
    private var emptyView: some View {
        VStack(spacing: Spacing.spacing6) {
            Image(systemName: "book.closed")
                .font(.system(size: 64))
                .foregroundColor(.neutralGray400)
            
            VStack(spacing: Spacing.spacing3) {
                Text("No hay cursos disponibles")
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(.neutralGray900)
                
                Text("Intenta recargar o vuelve más tarde")
                    .font(.bodyRegular)
                    .foregroundColor(.neutralGray600)
                    .multilineTextAlignment(.center)
            }
            
            Button("Recargar") {
                viewModel.refreshCourses()
            }
            .font(.buttonMedium)
            .foregroundColor(.neutralWhite)
            .padding(.horizontal, Spacing.spacing6)
            .padding(.vertical, Spacing.spacing3)
            .background(Color.primaryBlue)
            .cornerRadius(Radius.radiusMedium)
        }
        .padding(Spacing.spacing6)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("No hay cursos disponibles. Intenta recargar o vuelve más tarde")
    }
    
    private var courseListContent: some View {
        ScrollView {
            LazyVStack(spacing: Spacing.spacing4) {
                // Header section
                if !viewModel.searchText.isEmpty {
                    HStack {
                        Text("Resultados para '\(viewModel.searchText)'")
                            .font(.bodyEmphasized)
                            .foregroundColor(.neutralGray600)
                        Spacer()
                    }
                    .padding(.horizontal, Spacing.spacing4)
                    .padding(.top, Spacing.spacing2)
                }
                
                // Course grid
                LazyVGrid(columns: columns, spacing: Spacing.spacing4) {
                    ForEach(viewModel.filteredCourses) { course in
                        CourseCardView(course: course) {
                            viewModel.selectCourse(course)
                        }
                        .accessibilityAddTraits(.isButton)
                    }
                }
                .padding(.horizontal, Spacing.spacing4)
                .padding(.bottom, Spacing.spacing6)
            }
        }
        .accessibilityLabel("Lista de cursos")
    }
}

// MARK: - Preview
struct CourseListView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            // Normal state
            CourseListView()
                .previewDisplayName("Normal State")
            
            // Dark mode
            CourseListView()
                .preferredColorScheme(.dark)
                .previewDisplayName("Dark Mode")
            
            // iPhone SE
            CourseListView()
                .previewDevice("iPhone SE (3rd generation)")
                .previewDisplayName("iPhone SE")
            
            // iPad
            CourseListView()
                .previewDevice("iPad Pro (11-inch) (4th generation)")
                .previewDisplayName("iPad")
        }
    }
} 