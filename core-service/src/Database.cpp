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
            tests.push_back(test);
        }
        sqlite3_finalize(stmt);
    }
    
    sqlite3_close(db);
    return tests;
}

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

void Database::save_result(int user_id, int test_id, const std::vector<int>& answers, int score) {
    sqlite3* db;
    sqlite3_stmt* stmt;
    
    if (sqlite3_open(db_path.c_str(), &db) != SQLITE_OK) {
        return;
    }
    
    const char* sql = "INSERT INTO results (user_id, test_id, answers_json, score) VALUES (?, ?, ?, ?)";
    
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) == SQLITE_OK) {
        sqlite3_bind_int(stmt, 1, user_id);
        sqlite3_bind_int(stmt, 2, test_id);
        
        json answers_json = answers;
        std::string answers_str = answers_json.dump();
        sqlite3_bind_text(stmt, 3, answers_str.c_str(), -1, SQLITE_STATIC);
        
        sqlite3_bind_int(stmt, 4, score);
        
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);
    }
    
    sqlite3_close(db);
}
