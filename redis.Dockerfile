FROM redis:7-alpine

# Install additional tools
RUN apk add --no-cache curl

# Create configuration directory
RUN mkdir -p /usr/local/etc/redis

# Create Redis configuration
COPY --chown=redis:redis <<EOF /usr/local/etc/redis/redis.conf
# Redis Configuration for Blacklist System

# Network
bind 0.0.0.0
port 6379
tcp-backlog 511
timeout 300
tcp-keepalive 300

# General
daemonize no
supervised no
pidfile /var/run/redis.pid
loglevel notice
logfile ""
databases 16

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# Replication
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-ping-replica-period 10
repl-timeout 60
repl-disable-tcp-nodelay no
repl-backlog-size 1mb
repl-backlog-ttl 3600

# Security
requirepass ""
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""

# Clients
maxclients 10000

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency Monitor
latency-monitor-threshold 100

# Event Notification
notify-keyspace-events ""

# Advanced Config
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
client-query-buffer-limit 1gb
proto-max-bulk-len 512mb
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD redis-cli ping || exit 1

# Expose port
EXPOSE 6379

# Start Redis with custom configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]