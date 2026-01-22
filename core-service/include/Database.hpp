#pragma once
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

struct Question {
    int id;
    std::string text;
    std::vector<std::string> options;
    int correct_answer;
};

struct Test {
    int id;
    std::string title;
    std::string description;
    std::vector<Question> questions;
};

class Database {
private:
    std::string db_path;
    
    void init_tables();
    
public:
    Database(const std::string& path = "test.db");
    
    // Тесты
    std::vector<Test> get_all_tests();
    std::optional<Test> get_test(int test_id);
    int create_test(const std::string& title, const std::string& description);
    
    // Вопросы
    void add_question(int test_id, const std::string& text, 
                     const std::vector<std::string>& options, int correct_answer);
    
    // Результаты
    void save_result(int user_id, int test_id, const std::vector<int>& answers, int score);
    json get_user_results(int user_id);
};
