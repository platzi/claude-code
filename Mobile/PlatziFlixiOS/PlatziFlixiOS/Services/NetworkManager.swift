import Foundation

// MARK: - Network Manager
final class NetworkManager: NetworkService {
    static let shared = NetworkManager()
    
    private let urlSession: URLSession
    
    init(urlSession: URLSession = .shared) {
        self.urlSession = urlSession
    }
    
    func request(_ endpoint: APIEndpoint) async throws -> Data {
        guard let urlRequest = endpoint.urlRequest else {
            throw NetworkError.invalidURL
        }
        
        do {
            let (data, response) = try await urlSession.data(for: urlRequest)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw NetworkError.invalidResponse
            }
            
            guard 200...299 ~= httpResponse.statusCode else {
                throw NetworkError.requestFailed(statusCode: httpResponse.statusCode)
            }
            
            return data
            
        } catch {
            if error is NetworkError {
                throw error
            }
            
            if let urlError = error as? URLError {
                switch urlError.code {
                case .notConnectedToInternet, .networkConnectionLost:
                    throw NetworkError.networkUnavailable
                case .timedOut:
                    throw NetworkError.timeout
                default:
                    throw NetworkError.unknown(error)
                }
            }
            
            throw NetworkError.unknown(error)
        }
    }
}

// MARK: - Convenience methods
extension NetworkManager {
    func get<T: Codable>(_ endpoint: APIEndpoint, responseType: T.Type) async throws -> T {
        return try await request(endpoint, responseType: responseType)
    }
    
    func post<T: Codable>(_ endpoint: APIEndpoint, responseType: T.Type) async throws -> T {
        return try await request(endpoint, responseType: responseType)
    }
    
    func put<T: Codable>(_ endpoint: APIEndpoint, responseType: T.Type) async throws -> T {
        return try await request(endpoint, responseType: responseType)
    }
    
    func delete<T: Codable>(_ endpoint: APIEndpoint, responseType: T.Type) async throws -> T {
        return try await request(endpoint, responseType: responseType)
    }
    
    func patch<T: Codable>(_ endpoint: APIEndpoint, responseType: T.Type) async throws -> T {
        return try await request(endpoint, responseType: responseType)
    }
}

// MARK: - Request with body encoding
extension NetworkManager {
    func request<T: Codable, U: Codable>(_ endpoint: APIEndpoint, body: U, responseType: T.Type) async throws -> T {
        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let bodyData = try encoder.encode(body)
            
            // Create a modified endpoint with the encoded body
            let endpointWithBody = APIEndpointWithBody(
                baseURL: endpoint.baseURL,
                path: endpoint.path,
                method: endpoint.method,
                headers: endpoint.headers,
                parameters: endpoint.parameters,
                body: bodyData
            )
            
            return try await request(endpointWithBody, responseType: responseType)
            
        } catch {
            throw NetworkError.encodingError(error)
        }
    }
}

// MARK: - Helper struct for endpoints with body
private struct APIEndpointWithBody: APIEndpoint {
    let baseURL: String
    let path: String
    let method: HTTPMethod
    let headers: [String: String]?
    let parameters: [String: Any]?
    let body: Data?
} 
