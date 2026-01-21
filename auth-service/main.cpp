#include <iostream>
#include <string>
#include <map>
#include <httplib.h>

using namespace httplib;

std::map<std::string, std::string> users = {
    {"user1", "admin"},
    {"user2", "user"}
};

bool validate_token(const std::string& token) {
    return users.find(token) != users.end();
}

std::string get_role(const std::string& token) {
    auto it = users.find(token);
    if (it != users.end()) {
        return it->second;
    }
    return "unauthorized";
}

int main() {
    Server svr;

    svr.Get("/auth/validate", [](const Request& req, Response& res) {
        std::string token = req.get_param_value("token");
        if (token.empty()) {
            res.set_content(R"({"error": "Token is required"})", "application/json");
            res.status = 400;
            return;
        }

        if (validate_token(token)) {
            res.set_content(R"({"valid": true, "role": ")" + get_role(token) + "\"}", "application/json");
        } else {
            res.set_content(R"({"valid": false})", "application/json");
            res.status = 401;
        }
    });

    svr.Post("/auth/login", [](const Request& req, Response& res) {
        std::string fake_token = "user1";
        res.set_content(R"({"token": ")" + fake_token + "\"}", "application/json");
    });

    svr.Get("/health", [](const Request&, Response& res) {
        res.set_content(R"({"status": "ok"})", "application/json");
    });

    std::cout << "Auth service running on http://localhost:8081\n";
    svr.listen("0.0.0.0", 8081);

    return 0;
}
