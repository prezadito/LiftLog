/// APIService.swift
/// Example implementation for migrating to v2 API
///
/// Key changes from v1:
/// - Add /v2 to base URL
/// - No other changes required!

import Foundation

// MARK: - Configuration

enum APIEnvironment {
    case production
    case staging
    case development

    var baseURL: String {
        switch self {
        case .production:
            return "https://api.liftlog.com/v2"
        case .staging:
            return "https://staging.liftlog.com/v2"
        case .development:
            return "http://localhost:8000/v2"
        }
    }

    var websocketURL: String {
        switch self {
        case .production:
            return "wss://api.liftlog.com/ai-chat"
        case .staging:
            return "wss://staging.liftlog.com/ai-chat"
        case .development:
            return "ws://localhost:8000/ai-chat"
        }
    }
}

// MARK: - Models (No changes from v1)

struct CreateUserResponse: Codable {
    let id: UUID
    let lookup: String
    let password: String
}

struct GetUserResponse: Codable {
    let id: UUID
    let lookup: String
    let encryptedCurrentPlan: Data?
    let encryptedProfilePicture: Data?
    let encryptedName: Data?
    let encryptionIV: Data
    let rsaPublicKey: Data

    enum CodingKeys: String, CodingKey {
        case id, lookup
        case encryptedCurrentPlan = "encrypted_current_plan"
        case encryptedProfilePicture = "encrypted_profile_picture"
        case encryptedName = "encrypted_name"
        case encryptionIV = "encryption_iv"
        case rsaPublicKey = "rsa_public_key"
    }
}

struct PutUserDataRequest: Codable {
    let id: UUID
    let password: String
    let encryptedCurrentPlan: Data?
    let encryptedProfilePicture: Data?
    let encryptedName: Data?
    let encryptionIV: Data
    let rsaPublicKey: Data

    enum CodingKeys: String, CodingKey {
        case id, password
        case encryptedCurrentPlan = "encrypted_current_plan"
        case encryptedProfilePicture = "encrypted_profile_picture"
        case encryptedName = "encrypted_name"
        case encryptionIV = "encryption_iv"
        case rsaPublicKey = "rsa_public_key"
    }
}

// MARK: - API Service

class APIService {
    static let shared = APIService()

    private let environment: APIEnvironment
    private let session: URLSession

    init(environment: APIEnvironment = .production) {
        self.environment = environment

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: config)
    }

    var baseURL: String {
        environment.baseURL
    }

    // MARK: - User Endpoints

    /// Create a new user
    /// POST /v2/user/create
    func createUser() async throws -> CreateUserResponse {
        let url = URL(string: "\(baseURL)/user/create")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = "{}".data(using: .utf8)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(httpResponse.statusCode)
        }

        return try JSONDecoder().decode(CreateUserResponse.self, from: data)
    }

    /// Get user by ID or lookup
    /// GET /v2/user/{idOrLookup}
    func getUser(idOrLookup: String) async throws -> GetUserResponse {
        let url = URL(string: "\(baseURL)/user/\(idOrLookup)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(httpResponse.statusCode)
        }

        return try JSONDecoder().decode(GetUserResponse.self, from: data)
    }

    /// Update user data
    /// PUT /v2/user
    func updateUser(request: PutUserDataRequest) async throws {
        let url = URL(string: "\(baseURL)/user")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let encoder = JSONEncoder()
        urlRequest.httpBody = try encoder.encode(request)

        let (_, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(httpResponse.statusCode)
        }
    }

    // MARK: - AI Endpoints (require purchase token)

    /// Generate AI workout plan
    /// POST /v2/ai/workout
    /// Requires: Authorization: Bearer {AppStore} {ProToken}
    func generateAIWorkout(
        attributes: AIWorkoutAttributes,
        appStore: AppStore,
        purchaseToken: String
    ) async throws -> ProgramBlueprint {
        let url = URL(string: "\(baseURL)/ai/workout")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(appStore.rawValue) \(purchaseToken)",
                        forHTTPHeaderField: "Authorization")

        let body = ["attributes": attributes]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // Handle rate limiting
        if httpResponse.statusCode == 429 {
            if let retryAfter = httpResponse.value(forHTTPHeaderField: "Retry-After") {
                throw APIError.rateLimited(retryAfter: retryAfter)
            }
            throw APIError.rateLimited(retryAfter: nil)
        }

        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(httpResponse.statusCode)
        }

        return try JSONDecoder().decode(ProgramBlueprint.self, from: data)
    }
}

// MARK: - Supporting Types

enum AppStore: String {
    case web = "Web"
    case google = "Google"
    case apple = "Apple"
    case revenueCat = "RevenueCat"
}

enum APIError: Error {
    case invalidResponse
    case httpError(Int)
    case rateLimited(retryAfter: String?)
}

// Placeholder types
struct AIWorkoutAttributes: Codable {
    let age: Int
    let gender: String
    let weightKg: Double
    let experienceLevel: String
    let goals: String
    let daysPerWeek: Int

    enum CodingKeys: String, CodingKey {
        case age, gender, goals
        case weightKg = "weight_kg"
        case experienceLevel = "experience_level"
        case daysPerWeek = "days_per_week"
    }
}

struct ProgramBlueprint: Codable {
    let name: String
    let description: String
    let durationWeeks: Int
    let sessions: [SessionBlueprint]

    enum CodingKeys: String, CodingKey {
        case name, description, sessions
        case durationWeeks = "duration_weeks"
    }
}

struct SessionBlueprint: Codable {
    let name: String
    let estimatedDurationMinutes: Int
    let exercises: [ExerciseBlueprint]

    enum CodingKeys: String, CodingKey {
        case name, exercises
        case estimatedDurationMinutes = "estimated_duration_minutes"
    }
}

struct ExerciseBlueprint: Codable {
    let name: String
    let sets: Int
    let repsMin: Int
    let repsMax: Int
    let restSeconds: Int
    let notes: String?

    enum CodingKeys: String, CodingKey {
        case name, sets, notes
        case repsMin = "reps_min"
        case repsMax = "reps_max"
        case restSeconds = "rest_seconds"
    }
}
