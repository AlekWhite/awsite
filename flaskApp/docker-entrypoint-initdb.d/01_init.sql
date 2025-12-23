-- users table for auth
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- temperature data table
CREATE TABLE IF NOT EXISTS temperature_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    avg_temp FLOAT NOT NULL,
    CONSTRAINT check_temp_range CHECK (avg_temp >= -150 AND avg_temp <= 250)
);
CREATE INDEX IF NOT EXISTS idx_temperature_timestamp ON temperature_data(timestamp DESC);

-- trigger function to maintain 24-entry limit
CREATE OR REPLACE FUNCTION maintain_avg_temp_limit()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete oldest entries if we exceed 24
    DELETE FROM temperature_data
    WHERE id IN (
        SELECT id FROM temperature_data
        ORDER BY timestamp DESC
        OFFSET 24
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- trigger to automatically remove old entries
DROP TRIGGER IF EXISTS trigger_maintain_avg_temp_limit ON temperature_data;
CREATE TRIGGER trigger_maintain_avg_temp_limit
    AFTER INSERT ON temperature_data
    FOR EACH STATEMENT
    EXECUTE FUNCTION maintain_avg_temp_limit();

-- current temperature table (stores only the latest reading)
CREATE TABLE IF NOT EXISTS current_temperature (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_temp FLOAT NOT NULL,
    CONSTRAINT check_current_temp_range CHECK (current_temp >= -150 AND current_temp <= 250)
);

-- rgb light values table
CREATE TABLE IF NOT EXISTS rgb_light_vals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    red INTEGER NOT NULL CHECK (red >= 0 AND red <= 255),
    green INTEGER NOT NULL CHECK (green >= 0 AND green <= 255),
    blue INTEGER NOT NULL CHECK (blue >= 0 AND blue <= 255)
);

-- fish of the week table
CREATE TABLE IF NOT EXISTS fish_of_the_week (
    id SERIAL PRIMARY KEY,
    wiki_url VARCHAR(500) UNIQUE NOT NULL,
    fish_name VARCHAR(200) NOT NULL,
    last_chosen_week DATE NULL
);
CREATE INDEX IF NOT EXISTS idx_fish_last_chosen ON fish_of_the_week(last_chosen_week);

-- arduino state table
CREATE TABLE IF NOT EXISTS arduino (
    id SERIAL PRIMARY KEY,
    port VARCHAR(100) NOT NULL,
    state VARCHAR(20) NOT NULL CHECK (state IN ('offline', 'online', 'update'))
);
