#include "include/Database.hpp"
#include <sqlite3.h>
#include <iostream>

Database::Database(const std::string& path) : db_path(path) {
    init_tables();
}

void Database::init_tables() {
    sqlite3* db;
    char* err_msg = nullptr;
    
    if (sqlite3_open(db_path.c_str(), &db) != SQLITE_OK) {
        std::cerr << "Cannot open database: " << sqlite3_errmsg(db) << std::endl;
        return;
    }
    
    const char* sql = 
        "CREATE TABLE IF NOT EXISTS tests ("
        "   id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "   title TEXT NOT NULL,"
        "   description TEXT"
        ");"
        "CREATE TABLE IF NOT EXISTS questions ("
        "   id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "   test_id INTEGER,"
        "   text TEXT NOT NULL,"
        "   options_json TEXT,"
        "   correct_answer INTEGER,"
        "   FOREIGN KEY (test_id) REFERENCES tests(id)"
        ");"
        "CREATE TABLE IF NOT EXISTS results ("
        "   id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "   user_id INTEGER,"
        "   test_id INTEGER,"
        "   answers_json TEXT,"
        "   score INTEGER,"
        "   completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "   FOREIGN KEY (test_id) REFERENCES tests(id)"
        ");";
    
    if (sqlite3_exec(db, sql, nullptr, nullptr, &err_msg) != SQLITE_OK) {
        std::cerr << "SQL error: " << err_msg << std::endl;
        sqlite3_free(err_msg);
    }
    
    sqlite3_close(db);
}

std::vector<Test> Database::get_all_tests() {
    std::vector<Test> tests;
    sqlite3* db;
    sqlite3_stmt* stmt;
    
    if (sqlite3_open(db_path.c_str(), &db) != SQLITE_OK) {
        return tests;
    }
    
    const char* sql = "SELECT id, title, description FROM tests";
    
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) == SQLITE_OK) {
        while (sqlite3_step(stmt) == SQLITE_ROW) {
            Test test;
            test.id = sqlite3_column_int(stmt, 0);
            test.title = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1));
            test.description = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 2));
            
            // Получаем вопросы для этого теста
            sqlite3_stmt* q_stmt;
            std::string q_sql = "SELECT text, options_json, correct_answer FROM questions WHERE test_id = ?";
            if (sqlite3_prepare_v2(db, q_sql.c_str(), -1, &q_stmt, nullptr) == SQLITE_OK) {
                sqlite3_bind_int(q_stmt, 1, test.id);
                while (sqlite3_step(q_stmt) == SQLITE_ROW) {
                    Question q;
                    q.text = reinterpret_cast<const char*>(sqlite3_column_text(q_stmt, 0));
                    
                    // Парсим options из JSON
                    std::string options_json = reinterpret_cast<const char*>(sqlite3_column_text(q_stmt, 1));
                    try {
                        json j = json::parse(options_json);
                        for (const auto& item : j) {
                            q.options.push_back(item.get<std::string>());
                        }
                    } catch (...) {}
                    
                    q.correct_answer = sqlite3_column_int(q_stmt, 2);
                    test.questions.push_back(q);
                }
                sqlite3_finalize(q_stmt);
            }
            
            tests.push_back(test);
        }
        sqlite3_finalize(stmt);
    }
    
    sqlite3_close(db);
    return tests;
}

// Остальные методы аналогично...

int Database::create_test(const std::string& title, const std::string& description) {
    sqlite3* db;
    sqlite3_stmt* stmt;
    
    if (sqlite3_open(db_path.c_str(), &db) != SQLITE_OK) {
        return -1;
    }
    
    const char* sql = "INSERT INTO tests (title, description) VALUES (?, ?)";
    
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) == SQLITE_OK) {
        sqlite3_bind_text(stmt, 1, title.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_text(stmt, 2, description.c_str(), -1, SQLITE_STATIC);
        
        if (sqlite3_step(stmt) == SQLITE_DONE) {
            int id = sqlite3_last_insert_rowid(db);
            sqlite3_finalize(stmt);
            sqlite3_close(db);
            return id;
        }
    }
    
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return -1;
}
