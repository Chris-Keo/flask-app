CREATE DATABASE IF NOT EXISTS flask_app_db;

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    salary NUMERIC(10,2) DEFAULT 0,
    email VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    owner VARCHAR(100),
    budget NUMERIC(10,2) DEFAULT 0
);

INSERT INTO employees (name, department, salary, email)
VALUES
    ('Alice Johnson', 'Engineering', 75000.00, 'alice@example.com'),
    ('Bob Smith', 'Marketing', 65000.00, 'bob@example.com')
ON CONFLICT DO NOTHING;

INSERT INTO projects (name, status, owner, budget)
VALUES
    ('Website Redesign', 'active', 'Chris', 150000.00),
    ('Mobile App', 'planning', 'Maya', 80000.00')
ON CONFLICT DO NOTHING;
