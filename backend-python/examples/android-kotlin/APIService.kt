// APIService.kt
// Example implementation for migrating to v2 API
//
// Key changes from v1:
// - Update BASE_URL to include /v2/
// - No other changes required!

package com.liftlog.api

import com.google.gson.annotations.SerializedName
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.UUID
import java.util.concurrent.TimeUnit

// MARK: - Configuration

object APIConfig {
    const val PRODUCTION_URL = "https://api.liftlog.com/v2/"
    const val STAGING_URL = "https://staging.liftlog.com/v2/"
    const val DEVELOPMENT_URL = "http://10.0.2.2:8000/v2/"  // Android emulator

    const val WEBSOCKET_PRODUCTION = "wss://api.liftlog.com/ai-chat"
    const val WEBSOCKET_STAGING = "wss://staging.liftlog.com/ai-chat"
    const val WEBSOCKET_DEVELOPMENT = "ws://10.0.2.2:8000/ai-chat"

    fun getBaseUrl(environment: Environment): String {
        return when (environment) {
            Environment.PRODUCTION -> PRODUCTION_URL
            Environment.STAGING -> STAGING_URL
            Environment.DEVELOPMENT -> DEVELOPMENT_URL
        }
    }
}

enum class Environment {
    PRODUCTION,
    STAGING,
    DEVELOPMENT
}

enum class AppStore(val value: String) {
    WEB("Web"),
    GOOGLE("Google"),
    APPLE("Apple"),
    REVENUECAT("RevenueCat")
}

// MARK: - Models (No changes from v1)

data class CreateUserResponse(
    val id: UUID,
    val lookup: String,
    val password: String
)

data class GetUserResponse(
    val id: UUID,
    val lookup: String,
    @SerializedName("encrypted_current_plan")
    val encryptedCurrentPlan: ByteArray?,
    @SerializedName("encrypted_profile_picture")
    val encryptedProfilePicture: ByteArray?,
    @SerializedName("encrypted_name")
    val encryptedName: ByteArray?,
    @SerializedName("encryption_iv")
    val encryptionIV: ByteArray,
    @SerializedName("rsa_public_key")
    val rsaPublicKey: ByteArray
)

data class PutUserDataRequest(
    val id: UUID,
    val password: String,
    @SerializedName("encrypted_current_plan")
    val encryptedCurrentPlan: ByteArray?,
    @SerializedName("encrypted_profile_picture")
    val encryptedProfilePicture: ByteArray?,
    @SerializedName("encrypted_name")
    val encryptedName: ByteArray?,
    @SerializedName("encryption_iv")
    val encryptionIV: ByteArray,
    @SerializedName("rsa_public_key")
    val rsaPublicKey: ByteArray
)

data class GenerateAIWorkoutRequest(
    val attributes: AIWorkoutAttributes
)

data class AIWorkoutAttributes(
    val age: Int,
    val gender: String,
    @SerializedName("weight_kg")
    val weightKg: Double,
    @SerializedName("experience_level")
    val experienceLevel: String,
    val goals: String,
    @SerializedName("days_per_week")
    val daysPerWeek: Int,
    @SerializedName("additional_preferences")
    val additionalPreferences: String? = null
)

data class ProgramBlueprint(
    val name: String,
    val description: String,
    @SerializedName("duration_weeks")
    val durationWeeks: Int,
    val sessions: List<SessionBlueprint>
)

data class SessionBlueprint(
    val name: String,
    @SerializedName("estimated_duration_minutes")
    val estimatedDurationMinutes: Int,
    val exercises: List<ExerciseBlueprint>
)

data class ExerciseBlueprint(
    val name: String,
    val sets: Int,
    @SerializedName("reps_min")
    val repsMin: Int,
    @SerializedName("reps_max")
    val repsMax: Int,
    @SerializedName("rest_seconds")
    val restSeconds: Int,
    val notes: String? = null
)

// MARK: - API Interface

interface LiftLogAPI {

    // User Management
    @POST("user/create")
    suspend fun createUser(@Body request: Map<String, Any> = emptyMap()): CreateUserResponse

    @GET("user/{idOrLookup}")
    suspend fun getUser(@Path("idOrLookup") idOrLookup: String): GetUserResponse

    @PUT("user")
    suspend fun updateUser(@Body request: PutUserDataRequest)

    @POST("user/delete")
    suspend fun deleteUser(@Body request: Map<String, Any>)

    // AI Endpoints (require Authorization header)
    @POST("ai/workout")
    suspend fun generateAIWorkout(
        @Header("Authorization") authorization: String,
        @Body request: GenerateAIWorkoutRequest
    ): ProgramBlueprint

    @POST("ai/session")
    suspend fun generateAISession(
        @Header("Authorization") authorization: String,
        @Body request: GenerateAIWorkoutRequest
    ): SessionBlueprint
}

// MARK: - Interceptors

class AuthorizationInterceptor(
    private val appStore: AppStore,
    private val getToken: () -> String
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()

        // Only add auth to AI endpoints
        if (original.url.encodedPath.contains("/ai/")) {
            val token = getToken()
            val request = original.newBuilder()
                .header("Authorization", "Bearer ${appStore.value} $token")
                .build()
            return chain.proceed(request)
        }

        return chain.proceed(original)
    }
}

class RateLimitInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val response = chain.proceed(chain.request())

        // Handle rate limiting
        if (response.code == 429) {
            val retryAfter = response.header("Retry-After")
            // Log or handle rate limit
            println("Rate limited. Retry after: $retryAfter")
        }

        return response
    }
}

// MARK: - API Service

class APIService private constructor(
    private val environment: Environment
) {

    private val api: LiftLogAPI

    init {
        val client = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(RateLimitInterceptor())
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(APIConfig.getBaseUrl(environment))
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        api = retrofit.create(LiftLogAPI::class.java)
    }

    // Singleton instances
    companion object {
        @Volatile
        private var INSTANCE: APIService? = null

        fun getInstance(environment: Environment = Environment.PRODUCTION): APIService {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: APIService(environment).also { INSTANCE = it }
            }
        }
    }

    // User endpoints
    suspend fun createUser(): CreateUserResponse {
        return api.createUser()
    }

    suspend fun getUser(idOrLookup: String): GetUserResponse {
        return api.getUser(idOrLookup)
    }

    suspend fun updateUser(request: PutUserDataRequest) {
        api.updateUser(request)
    }

    // AI endpoints
    suspend fun generateWorkout(
        attributes: AIWorkoutAttributes,
        appStore: AppStore,
        purchaseToken: String
    ): ProgramBlueprint {
        val auth = "Bearer ${appStore.value} $purchaseToken"
        return api.generateAIWorkout(auth, GenerateAIWorkoutRequest(attributes))
    }
}

// MARK: - Usage Example

/*
// In your Activity or ViewModel:

class WorkoutViewModel : ViewModel() {
    private val apiService = APIService.getInstance(Environment.PRODUCTION)

    fun loadUser(userId: String) {
        viewModelScope.launch {
            try {
                val user = apiService.getUser(userId)
                // Handle user data
                println("User: ${user.lookup}")
            } catch (e: Exception) {
                // Handle error
                println("Error: ${e.message}")
            }
        }
    }

    fun generateWorkout() {
        viewModelScope.launch {
            val attributes = AIWorkoutAttributes(
                age = 30,
                gender = "male",
                weightKg = 75.0,
                experienceLevel = "Intermediate",
                goals = "Build muscle",
                daysPerWeek = 4
            )

            try {
                val program = apiService.generateWorkout(
                    attributes = attributes,
                    appStore = AppStore.GOOGLE,
                    purchaseToken = "your.purchase.token.here"
                )
                // Handle program
                println("Program: ${program.name}")
            } catch (e: Exception) {
                // Handle error (including rate limiting)
                println("Error: ${e.message}")
            }
        }
    }
}
*/
