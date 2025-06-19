import Foundation

protocol NetworkService {
    func request<T: Codable>(_ endpoint: APIEndpoint, responseType: T.Type) async throws -> T
    func request(_ endpoint: APIEndpoint) async throws -> Data
}

// MARK: - Default implementation
extension NetworkService {
    func request<T: Codable>(_ endpoint: APIEndpoint, responseType: T.Type) async throws -> T {
        let data = try await request(endpoint)
        
        do {
            let decoder = JSONDecoder()
            // Configure decoder if needed (e.g., date formatting)
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(T.self, from: data)
        } catch {
            throw NetworkError.decodingError(error)
        }
    }
} 