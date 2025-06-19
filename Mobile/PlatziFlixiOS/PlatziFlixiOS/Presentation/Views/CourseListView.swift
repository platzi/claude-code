import SwiftUI

/// Main view that displays the list of courses
struct CourseListView: View {
    @StateObject private var viewModel = CourseListViewModel()
    @State private var showSearchBar = false
    
    var body: some View {
        NavigationView {
            ZStack {
                // Background color - using system background for better dark mode
                Color.groupedBackground
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
                .foregroundColor(.secondary)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Cargando cursos")
    }
    
    private var emptyView: some View {
        VStack(spacing: Spacing.spacing6) {
            Image(systemName: "book.closed")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            
            VStack(spacing: Spacing.spacing3) {
                Text("No hay cursos disponibles")
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)
                
                Text("Intenta recargar o vuelve más tarde")
                    .font(.bodyRegular)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            Button("Recargar") {
                viewModel.refreshCourses()
            }
            .font(.buttonMedium)
            .foregroundColor(.white)
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
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                    .padding(.horizontal, Spacing.spacing4)
                    .padding(.top, Spacing.spacing2)
                }
                
                // Course list - Changed from grid to vertical stack
                LazyVStack(spacing: Spacing.spacing4) {
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

// MARK: - Previews
#Preview("Normal State") {
    CourseListView()
}

#Preview("Dark Mode") {
    CourseListView()
        .preferredColorScheme(.dark)
}

#Preview("iPhone SE") {
    CourseListView()
        .previewDevice("iPhone SE (3rd generation)")
}

#Preview("iPad") {
    CourseListView()
        .previewDevice("iPad Pro (11-inch) (4th generation)")
} 