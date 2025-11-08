-- Schema for Users service (MySQL)

-- 1. Create database
CREATE DATABASE IF NOT EXISTS user_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 2. Use database
USE user_db;

-- 3. Roles table
CREATE TABLE IF NOT EXISTS roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name ENUM('User', 'PT', 'Admin') NOT NULL
);

-- 4. Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    gender ENUM('Nam', 'Nữ', 'Khác'),
    height_cm DECIMAL(5,2),
    weight_kg DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);
