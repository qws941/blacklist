FROM postgres:15-alpine

# Set environment variables
ENV POSTGRES_DB=blacklist
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# Install additional tools
RUN apk add --no-cache curl

# Create initialization directory
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy initialization scripts
COPY --chown=postgres:postgres <<EOF /docker-entrypoint-initdb.d/01-init-schema.sql
-- Blacklist Management System Database Schema

-- Create blacklist_ips table
CREATE TABLE IF NOT EXISTS blacklist_ips (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL UNIQUE,
    source VARCHAR(50) NOT NULL,
    reason TEXT,
    threat_level VARCHAR(20) DEFAULT 'MEDIUM',
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'
);

-- Create system_logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,
    component VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'
);

-- Create monitoring_data table
CREATE TABLE IF NOT EXISTS monitoring_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    source VARCHAR(50) NOT NULL
);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL UNIQUE,
    key_value TEXT NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    permissions JSONB DEFAULT '{}'
);

-- Create collection_history table
CREATE TABLE IF NOT EXISTS collection_history (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    collection_type VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'RUNNING',
    records_collected INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

-- Create user_activities table
CREATE TABLE IF NOT EXISTS user_activities (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(200),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Create notification_settings table
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    setting_name VARCHAR(100) NOT NULL UNIQUE,
    setting_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source ON blacklist_ips(source);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_threat_level ON blacklist_ips(threat_level);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_is_active ON blacklist_ips(is_active);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_first_seen ON blacklist_ips(first_seen);

CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_component ON system_logs(component);

CREATE INDEX IF NOT EXISTS idx_monitoring_data_timestamp ON monitoring_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_monitoring_data_metric_name ON monitoring_data(metric_name);
CREATE INDEX IF NOT EXISTS idx_monitoring_data_source ON monitoring_data(source);

CREATE INDEX IF NOT EXISTS idx_collection_history_source ON collection_history(source);
CREATE INDEX IF NOT EXISTS idx_collection_history_status ON collection_history(status);
CREATE INDEX IF NOT EXISTS idx_collection_history_start_time ON collection_history(start_time);

CREATE INDEX IF NOT EXISTS idx_user_activities_timestamp ON user_activities(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_activities_action ON user_activities(action);

-- Insert default notification settings
INSERT INTO notification_settings (setting_name, setting_value) VALUES
('email_alerts', '{"enabled": true, "recipients": ["admin@example.com"], "threshold": "HIGH"}'),
('slack_webhook', '{"enabled": false, "webhook_url": "", "channel": "#security"}'),
('sms_alerts', '{"enabled": false, "phone_numbers": [], "threshold": "CRITICAL"}')
ON CONFLICT (setting_name) DO NOTHING;

-- Create function to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_last_updated_column()
RETURNS TRIGGER AS \$\$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
\$\$ language 'plpgsql';

-- Create trigger for blacklist_ips table
CREATE TRIGGER update_blacklist_ips_last_updated 
    BEFORE UPDATE ON blacklist_ips 
    FOR EACH ROW 
    EXECUTE FUNCTION update_last_updated_column();

-- Create trigger for notification_settings table
CREATE OR REPLACE FUNCTION update_notification_settings_updated_at()
RETURNS TRIGGER AS \$\$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
\$\$ language 'plpgsql';

CREATE TRIGGER update_notification_settings_updated_at 
    BEFORE UPDATE ON notification_settings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_notification_settings_updated_at();
EOF

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pg_isready -U postgres -d blacklist || exit 1

# Expose port
EXPOSE 5432