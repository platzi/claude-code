package com.espaciotiago.platziflixandroid.data.network

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Network module for Retrofit configuration
 */
object NetworkModule {
    
    // Use 10.0.2.2 for Android emulator to access localhost
    // Use your actual IP address for physical devices
    private const val BASE_URL = "http://10.0.2.2:8000/"
    private const val TIMEOUT_SECONDS = 30L
    
    /**
     * Creates OkHttpClient with logging interceptor
     */
    private fun createOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .readTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .writeTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .build()
    }
    
    /**
     * Creates Retrofit instance
     */
    private fun createRetrofit(): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(createOkHttpClient())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    /**
     * Provides ApiService instance
     */
    fun provideApiService(): ApiService {
        return createRetrofit().create(ApiService::class.java)
    }
} 