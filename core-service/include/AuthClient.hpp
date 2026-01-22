#pragma once
#include <string>
#include <optional>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

struct UserInfo {
    std::string username;
    std::string role;
    bool valid;
};

class AuthClient {
private:
    std::string auth_service_url;
    
public:
    AuthClient(const std::string& url = "http://auth-service:8081");
    
    std::optional<UserInfo> validate_token(const std::string& token);
    std::optional<json> get_user_info(const std::string& token);
    bool is_admin(const std::string& token);
};
