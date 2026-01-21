package main

import (
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "github.com/gorilla/mux"
    _ "github.com/lib/pq"
)

// Структуры данных
type Survey struct {
    ID    int    `json:"id"`
    Title string `json:"title"`
}

type Question struct {
    ID       int      `json:"id"`
    SurveyID int      `json:"survey_id"`
    Text     string   `json:"text"`
    Type     string   `json:"type"` // "text", "radio", "checkbox"
    Options  []string `json:"options,omitempty"`
}

var db *sql.DB

func main() {
    // Подключение к БД
    connStr := os.Getenv("DATABASE_URL")
    if connStr == "" {
        connStr = "postgresql://admin:password@postgres:5432/survey_db?sslmode=disable"
    }
    
    var err error
    db, err = sql.Open("postgres", connStr)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()
    
    // Создаём таблицы если их нет
    initDB()
    
    // Настраиваем маршруты
    r := mux.NewRouter()
    
    // API endpoints
    r.HandleFunc("/api/health", healthCheck).Methods("GET")
    r.HandleFunc("/api/surveys", getSurveys).Methods("GET")
    r.HandleFunc("/api/surveys/{id}", getSurvey).Methods("GET")
    r.HandleFunc("/api/surveys/{id}/submit", submitAnswers).Methods("POST")
    
    // Запуск сервера
    port := ":8080"
    fmt.Printf("Core service running on port %s\n", port)
    log.Fatal(http.ListenAndServe(port, r))
}

func initDB() {
    queries := []string{
        `CREATE TABLE IF NOT EXISTS surveys (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )`,
        `CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER REFERENCES surveys(id),
            text TEXT NOT NULL,
            type VARCHAR(50) NOT NULL,
            options TEXT[]
        )`,
        `CREATE TABLE IF NOT EXISTS answers (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER,
            question_id INTEGER,
            user_id VARCHAR(100),
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )`,
    }
    
    for _, query := range queries {
        _, err := db.Exec(query)
        if err != nil {
            log.Printf("Error creating table: %v", err)
        }
    }
    
    // Добавляем тестовые данные
    addTestData()
}

func addTestData() {
    // Проверяем есть ли уже данные
    var count int
    db.QueryRow("SELECT COUNT(*) FROM surveys").Scan(&count)
    
    if count == 0 {
        // Добавляем тестовый опрос
        db.Exec("INSERT INTO surveys (title) VALUES ($1)", "Оценка курса программирования")
        db.Exec("INSERT INTO surveys (title) VALUES ($1)", "Опрос об университете")
        
        // Добавляем вопросы к первому опросу
        db.Exec(`INSERT INTO questions (survey_id, text, type, options) 
                VALUES (1, 'Как вы оцениваете сложность курса?', 'radio', 
                ARRAY['Слишком легко', 'В самый раз', 'Слишком сложно'])`)
        
        db.Exec(`INSERT INTO questions (survey_id, text, type, options) 
                VALUES (1, 'Что понравилось больше всего?', 'checkbox',
                ARRAY['Лекции', 'Практика', 'Проект', 'Преподаватель'])`)
        
        db.Exec(`INSERT INTO questions (survey_id, text, type) 
                VALUES (1, 'Ваши пожелания на будущее', 'text')`)
    }
}

// Обработчики API
func healthCheck(w http.ResponseWriter, r *http.Request) {
    json.NewEncoder(w).Encode(map[string]string{"status": "OK", "service": "core"})
}

func getSurveys(w http.ResponseWriter, r *http.Request) {
    rows, err := db.Query("SELECT id, title FROM surveys")
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    defer rows.Close()
    
    var surveys []Survey
    for rows.Next() {
        var s Survey
        if err := rows.Scan(&s.ID, &s.Title); err != nil {
            continue
        }
        surveys = append(surveys, s)
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(surveys)
}

func getSurvey(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    surveyID := vars["id"]
    
    // Получаем опрос
    var survey Survey
    err := db.QueryRow("SELECT id, title FROM surveys WHERE id = $1", surveyID).
        Scan(&survey.ID, &survey.Title)
    
    if err != nil {
        http.Error(w, "Survey not found", http.StatusNotFound)
        return
    }
    
    // Получаем вопросы
    rows, err := db.Query(`
        SELECT id, text, type, options 
        FROM questions 
        WHERE survey_id = $1 
        ORDER BY id`, surveyID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    defer rows.Close()
    
    var questions []Question
    for rows.Next() {
        var q Question
        var options []byte
        err := rows.Scan(&q.ID, &q.Text, &q.Type, &options)
        if err == nil && options != nil {
            json.Unmarshal(options, &q.Options)
        }
        questions = append(questions, q)
    }
    
    response := map[string]interface{}{
        "survey":    survey,
        "questions": questions,
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func submitAnswers(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    surveyID := vars["id"]
    
    var answers map[string]string
    if err := json.NewDecoder(r.Body).Decode(&answers); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    userID := "test_user" // В реальности из авторизации
    
    for qID, answer := range answers {
        _, err := db.Exec(`
            INSERT INTO answers (survey_id, question_id, user_id, answer)
            VALUES ($1, $2, $3, $4)`,
            surveyID, qID, userID, answer)
        if err != nil {
            log.Printf("Error saving answer: %v", err)
        }
    }
    
    json.NewEncoder(w).Encode(map[string]string{
        "status": "success", 
        "message": "Answers saved",
    })
}
