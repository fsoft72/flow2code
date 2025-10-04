CREATE TABLE User (
    id VARCHAR(200) PRIMARY KEY,
    domain VARCHAR(50),
    email VARCHAR(200),
    username VARCHAR(50) NOT NULL,
    name VARCHAR(50),
    lastname VARCHAR(50),
    perms TEXT,
    enabled INTEGER,
    level INTEGER,
    password VARCHAR(200),
    code VARCHAR(200),
    refresh_token VARCHAR(200),
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_domain ON User(domain);

CREATE INDEX idx_user_enabled ON User(enabled);