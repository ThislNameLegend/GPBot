#include "include/AuthClient.hpp"
#include <curl/curl.h>
#include <iostream>

// Callback для curl
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* output) {
    size_t total_size = size * nmemb;
    output->append((char*)contents, total_size);
    return total_size;
}

AuthClient::AuthClient(const std::string& url) : auth_service_url(url) {}

std::optional<UserInfo> AuthClient::validate_token(const std::string& token) {
    CURL* curl = curl_easy_init();
    if (!curl) return std::nullopt;
    
    std::string url = auth_service_url + "/auth/validate?token=" + token;
    std::string response_data;
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
    
    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    
    if (res != CURLE_OK) {
        std::cerr << "CURL error: " << curl_easy_strerror(res) << std::endl;
        return std::nullopt;
    }
    
    try {
        auto j = json::parse(response_data);
        UserInfo info;
        info.valid = j.value("valid", false);
        info.username = j.value("user", "");
        info.role = j.value("role", "user");
        return info;
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<json> AuthClient::get_user_info(const std::string& token) {
    CURL* curl = curl_easy_init();
    if (!curl) return std::nullopt;
    
    std::string url = auth_service_url + "/auth/user";
    std::string response_data;
    
    struct curl_slist* headers = nullptr;
    std::string auth_header = "Authorization: Bearer " + token;
    headers = curl_slist_append(headers, auth_header.c_str());
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
    
    CURLcode res = curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    
    if (res != CURLE_OK) {
        return std::nullopt;
    }
    
    try {
        return json::parse(response_data);
    } catch (...) {
        return std::nullopt;
    }
}

bool AuthClient::is_admin(const std::string& token) {
    auto info = validate_token(token);
    return info.has_value() && info->valid && info->role == "admin";
}
