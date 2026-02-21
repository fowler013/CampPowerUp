-- Database initialization script for Camp Power-Up
-- This runs when PostgreSQL container starts for the first time

-- Create main campers table (historical data)
CREATE TABLE IF NOT EXISTS campers (
    id SERIAL PRIMARY KEY,
    timestamp VARCHAR(50),
    email_address VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_returning VARCHAR(10),
    age INTEGER,
    grade VARCHAR(50),
    game_behavior TEXT,
    rating_restrictions TEXT,
    bringing_switch VARCHAR(10),
    consent_social_media VARCHAR(10),
    has_sensory_issues VARCHAR(10),
    sensory_description TEXT,
    has_allergies VARCHAR(10),
    allergy_description TEXT,
    favorite_games TEXT,
    top_5_games TEXT,
    console_games TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create registration submissions table (new registrations)
CREATE TABLE IF NOT EXISTS registrations (
    id SERIAL PRIMARY KEY,
    submission_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    parent_email VARCHAR(255) NOT NULL,
    parent_name VARCHAR(255),
    parent_phone VARCHAR(50),
    child_first_name VARCHAR(100) NOT NULL,
    child_last_name VARCHAR(100) NOT NULL,
    child_age INTEGER,
    child_grade VARCHAR(50),
    is_returning_camper BOOLEAN DEFAULT FALSE,
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(50),
    emergency_contact_relationship VARCHAR(100),
    medical_conditions TEXT,
    dietary_restrictions TEXT,
    allergies TEXT,
    medications TEXT,
    behavioral_considerations TEXT,
    pickup_instructions TEXT,
    consent_photos BOOLEAN DEFAULT FALSE,
    consent_social_media BOOLEAN DEFAULT FALSE,
    additional_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_campers_name ON campers(first_name, last_name);
CREATE INDEX IF NOT EXISTS idx_campers_age ON campers(age);
CREATE INDEX IF NOT EXISTS idx_campers_returning ON campers(is_returning);

CREATE INDEX IF NOT EXISTS idx_registrations_email ON registrations(parent_email);
CREATE INDEX IF NOT EXISTS idx_registrations_child_name ON registrations(child_first_name, child_last_name);
CREATE INDEX IF NOT EXISTS idx_registrations_timestamp ON registrations(timestamp);
CREATE INDEX IF NOT EXISTS idx_registrations_returning ON registrations(is_returning_camper);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO campuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO campuser;