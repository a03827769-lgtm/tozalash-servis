CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    telegram_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    phone VARCHAR(255),
    language VARCHAR(10) DEFAULT 'uz',
    city VARCHAR(255) DEFAULT 'Toshkent',
    total_orders INTEGER DEFAULT 0,
    total_spent DOUBLE DEFAULT 0,
    rating DOUBLE DEFAULT 5.0,
    churn_risk DOUBLE DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    referral_code VARCHAR(20) UNIQUE,
    referred_by INTEGER,
    loyalty_points INTEGER DEFAULT 0,
    gold_status_notified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(referred_by) REFERENCES clients(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(255) UNIQUE,
    client_id INTEGER,
    client_telegram_id VARCHAR(255),
    service_type VARCHAR(255),
    service_name VARCHAR(255),
    quantity DOUBLE,
    unit VARCHAR(50),
    price_per_unit DOUBLE,
    surge_multiplier DOUBLE DEFAULT 1.0,
    total_price DOUBLE,
    address TEXT,
    scheduled_date VARCHAR(50),
    scheduled_time VARCHAR(50),
    status VARCHAR(50) DEFAULT 'yangi',
    worker_ids TEXT,
    worker_names TEXT,
    before_photo TEXT,
    after_photo TEXT,
    qa_approved INTEGER DEFAULT 0,
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'kutilmoqda',
    notes TEXT,
    is_eco_friendly BOOLEAN DEFAULT FALSE,
    custom_checklist TEXT,
    lat DOUBLE,
    lng DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(255),
    telegram_id VARCHAR(255) UNIQUE,
    telegram_username VARCHAR(255),
    specialization VARCHAR(255),
    is_active INTEGER DEFAULT 1,
    is_available INTEGER DEFAULT 1,
    total_jobs INTEGER DEFAULT 0,
    monthly_salary DOUBLE DEFAULT 0,
    balance DOUBLE DEFAULT 0,
    rating DOUBLE DEFAULT 5.0,
    gps_lat DOUBLE,
    gps_lon DOUBLE,
    last_location_update TIMESTAMP NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS finance (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    type VARCHAR(50),
    category VARCHAR(255),
    amount DOUBLE,
    description TEXT,
    order_id INTEGER,
    date VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_learning (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    context_type VARCHAR(255),
    input_data TEXT,
    output_data TEXT,
    success INTEGER,
    feedback_score DOUBLE,
    improvement TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channel_posts (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    platform VARCHAR(50),
    content TEXT,
    media_url TEXT,
    post_type VARCHAR(50),
    scheduled_at TIMESTAMP NULL,
    posted_at TIMESTAMP NULL,
    status VARCHAR(50) DEFAULT 'kutilmoqda',
    engagement_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    platform VARCHAR(50),
    url VARCHAR(255),
    phone VARCHAR(255),
    services TEXT,
    price_info TEXT,
    followers_count INTEGER,
    last_post_date VARCHAR(50),
    strengths TEXT,
    weaknesses TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    report_date VARCHAR(50) UNIQUE,
    orders_count INTEGER DEFAULT 0,
    completed_orders INTEGER DEFAULT 0,
    total_revenue DOUBLE DEFAULT 0,
    new_clients INTEGER DEFAULT 0,
    messages_received INTEGER DEFAULT 0,
    messages_answered INTEGER DEFAULT 0,
    ai_improvements TEXT,
    competitor_insights TEXT,
    tomorrow_plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    telegram_id VARCHAR(255),
    platform VARCHAR(50) DEFAULT 'telegram',
    role VARCHAR(50),
    message TEXT,
    state VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_states (
    telegram_id VARCHAR(255) PRIMARY KEY,
    state VARCHAR(255) DEFAULT 'idle',
    context TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
