#include <iostream>
#include <httplib.h>
#include <nlohmann/json.hpp>
#include "include/AuthClient.hpp"
#include "include/Database.hpp"

using json = nlohmann::json;
using namespace httplib;

std::string extract_token(const Request& req) {
    auto auth_header = req.get_header_value("Authorization");
    if (auth_header.find("Bearer ") == 0) {
        return auth_header.substr(7);
    }
    return req.get_param_value("token");
}

int main() {
    Server svr;
    AuthClient auth_client("http://auth-service:8081");
    Database db;
    
    svr.Get("/health", [](const Request&, Response& res) {
        json response = {
            {"status", "ok"},
            {"service", "core"},
            {"version", "1.0"}
        };
        res.set_content(response.dump(), "application/json");
    });
    
    svr.Get("/api/tests", [&](const Request& req, Response& res) {
        std::string token = extract_token(req);
        auto user_info = auth_client.validate_token(token);
        
        if (!user_info.has_value() || !user_info->valid) {
            res.status = 401;
            res.set_content(json{{"error", "Unauthorized"}}.dump(), "application/json");
            return;
        }
        
        auto tests = db.get_all_tests();
        json result = json::array();
        
        for (const auto& test : tests) {
            result.push_back({
                {"id", test.id},
                {"title", test.title},
                {"description", test.description},
                {"questions_count", static_cast<int>(test.questions.size())}
            });
        }
        
        res.set_content(result.dump(), "application/json");
    });
    
    svr.Get(R"(/api/tests/(\d+))", [&](const Request& req, Response& res) {
        int test_id = std::stoi(req.matches[1]);
        std::string token = extract_token(req);
        
        auto user_info = auth_client.validate_token(token);
        if (!user_info.has_value() || !user_info->valid) {
            res.status = 401;
            res.set_content(json{{"error", "Unauthorized"}}.dump(), "application/json");
            return;
        }
        
        auto test_opt = db.get_test(test_id);
        if (!test_opt.has_value()) {
            res.status = 404;
            res.set_content(json{{"error", "Test not found"}}.dump(), "application/json");
            return;
        }
        
        auto& test = test_opt.value();
        json result = {
            {"id", test.id},
            {"title", test.title},
            {"description", test.description},
            {"questions", json::array()}
        };
        
        for (const auto& q : test.questions) {
            json question = {
                {"id", q.id},
                {"text", q.text},
                {"options", q.options}
            };
            result["questions"].push_back(question);
        }
        
        res.set_content(result.dump(), "application/json");
    });
    
    svr.Post(R"(/api/tests/(\d+)/submit)", [&](const Request& req, Response& res) {
        int test_id = std::stoi(req.matches[1]);
        std::string token = extract_token(req);
        
        auto user_info = auth_client.validate_token(token);
        if (!user_info.has_value() || !user_info->valid) {
            res.status = 401;
            res.set_content(json{{"error", "Unauthorized"}}.dump(), "application/json");
            return;
        }
        
        json body;
        try {
            body = json::parse(req.body);
        } catch (...) {
            res.status = 400;
            res.set_content(json{{"error", "Invalid JSON"}}.dump(), "application/json");
            return;
        }
        
        auto answers = body.value("answers", json::array());
        std::vector<int> answer_vec;
        for (const auto& a : answers) {
            answer_vec.push_back(a.get<int>());
        }
        
        auto test_opt = db.get_test(test_id);
        if (!test_opt.has_value()) {
            res.status = 404;
            res.set_content(json{{"error", "Test not found"}}.dump(), "application/json");
            return;
        }
        
        auto& test = test_opt.value();
        int correct = 0;
        for (size_t i = 0; i < std::min(answer_vec.size(), test.questions.size()); i++) {
            if (test.questions[i].correct_answer == answer_vec[i]) {
                correct++;
            }
        }
        
        int score = (test.questions.size() > 0) ? (correct * 100) / test.questions.size() : 0;
        
        int user_id = 1001;
        db.save_result(user_id, test_id, answer_vec, score);
        
        json result = {
            {"test_id", test_id},
            {"user_id", user_id},
            {"total_questions", static_cast<int>(test.questions.size())},
            {"correct_answers", correct},
            {"score", score},
            {"passed", score >= 70}
        };
        
        res.set_content(result.dump(), "application/json");
    });
    
    std::cout << "✅ Core service (C++) running on http://0.0.0.0:8080\n";
    std::cout << "🔗 Auth service: http://auth-service:8081\n";
    
    svr.listen("0.0.0.0", 8080);
    return 0;
}
