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
-- Blacklist Management System Database Schema (Data-free Schema Only)

-- Create api_keys table
CREATE TABLE public.api_keys (
    id SERIAL PRIMARY KEY,
    key_name character varying(100) NOT NULL UNIQUE,
    key_hash character varying(255) NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_used timestamp without time zone,
    permissions jsonb,
    rate_limit integer DEFAULT 1000,
    expires_at timestamp without time zone
);

-- Create blacklist_ips table
CREATE TABLE public.blacklist_ips (
    id SERIAL PRIMARY KEY,
    ip_address inet NOT NULL UNIQUE,
    reason text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    source character varying(100) DEFAULT 'manual'::character varying,
    confidence_level integer DEFAULT 5,
    category character varying(50) DEFAULT 'unknown'::character varying,
    last_seen timestamp without time zone,
    detection_count integer DEFAULT 1
);

-- Create collection_credentials table
CREATE TABLE public.collection_credentials (
    id SERIAL PRIMARY KEY,
    service_name character varying(50) NOT NULL UNIQUE,
    username character varying(100),
    password character varying(255),
    api_key character varying(255),
    additional_data json,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Create collection_history table
CREATE TABLE public.collection_history (
    id SERIAL PRIMARY KEY,
    source_name character varying(100) NOT NULL,
    collection_type character varying(50),
    items_collected integer DEFAULT 0,
    success boolean DEFAULT true,
    error_message text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms integer,
    data_quality_score numeric,
    next_collection timestamp without time zone
);

-- Create monitoring_data table
CREATE TABLE public.monitoring_data (
    id SERIAL PRIMARY KEY,
    metric_name character varying(100) NOT NULL,
    metric_value text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tags jsonb,
    numeric_value numeric,
    unit character varying(20),
    alert_threshold numeric
);

-- Create notification_settings table
CREATE TABLE public.notification_settings (
    id SERIAL PRIMARY KEY,
    user_id character varying(100),
    notification_type character varying(50) NOT NULL,
    enabled boolean DEFAULT true,
    settings jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Create system_logs table
CREATE TABLE public.system_logs (
    id SERIAL PRIMARY KEY,
    level character varying(20) NOT NULL,
    message text NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    source character varying(100),
    context jsonb,
    request_id character varying(50),
    user_agent text,
    ip_address inet
);

-- Create user_activities table
CREATE TABLE public.user_activities (
    id SERIAL PRIMARY KEY,
    user_id character varying(100),
    action character varying(100) NOT NULL,
    resource_type character varying(50),
    resource_id character varying(100),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ip_address inet,
    user_agent text,
    success boolean DEFAULT true
);

-- Create indexes for better performance
CREATE INDEX idx_activities_action ON public.user_activities USING btree (action);
CREATE INDEX idx_activities_timestamp ON public.user_activities USING btree ("timestamp");
CREATE INDEX idx_activities_user ON public.user_activities USING btree (user_id);
CREATE INDEX idx_blacklist_ips_active ON public.blacklist_ips USING btree (is_active);
CREATE INDEX idx_blacklist_ips_category ON public.blacklist_ips USING btree (category);
CREATE INDEX idx_blacklist_ips_created ON public.blacklist_ips USING btree (created_at);
CREATE INDEX idx_blacklist_ips_source ON public.blacklist_ips USING btree (source);
CREATE INDEX idx_collection_source ON public.collection_history USING btree (source_name);
CREATE INDEX idx_collection_success ON public.collection_history USING btree (success);
CREATE INDEX idx_collection_timestamp ON public.collection_history USING btree ("timestamp");
CREATE INDEX idx_monitoring_metric ON public.monitoring_data USING btree (metric_name);
CREATE INDEX idx_monitoring_timestamp ON public.monitoring_data USING btree ("timestamp");
CREATE INDEX idx_system_logs_level ON public.system_logs USING btree (level);
CREATE INDEX idx_system_logs_source ON public.system_logs USING btree (source);
CREATE INDEX idx_system_logs_timestamp ON public.system_logs USING btree ("timestamp");

-- NO DATA INSERTION - Schema only for clean deployment
EOF

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pg_isready -U postgres -d blacklist || exit 1

# Expose port
EXPOSE 5432