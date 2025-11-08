# bỏ vào code sql trong mysql rồi chạy
-- Tạo bảng ROLES
CREATE TABLE roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name ENUM('User', 'PT', 'Admin') NOT NULL
);

-- Tạo bảng USERS
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    gender ENUM('Nam', 'Nữ', 'Khác'),
    height_cm DECIMAL(5, 2),
    weight_kg DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) 
        REFERENCES roles(role_id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE
);

-- Chèn dữ liệu mẫu cho ROLES
INSERT INTO roles (role_name) VALUES
('User'), ('PT'), ('Admin');

-- Chèn dữ liệu mẫu cho USERS (Mật khẩu đã được hash)
INSERT INTO users 
    (role_id, first_name, last_name, email, password_hash, gender, height_cm, weight_kg) 
VALUES
(
    1, 'Admin', 'Quản Trị', 'admin@app.com', 
    '$2b$12$FZXVSmaYUVe/9FPnAj2Z3ehYf5lVPfbeFVUzkwiAHM4SwlMF1Gat.', 
    'Khác', NULL, NULL
);