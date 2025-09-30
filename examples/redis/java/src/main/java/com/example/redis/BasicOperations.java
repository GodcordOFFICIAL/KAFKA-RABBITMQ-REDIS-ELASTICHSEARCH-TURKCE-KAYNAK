package com.example.redis;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;
import redis.clients.jedis.Pipeline;
import redis.clients.jedis.Response;
import redis.clients.jedis.Transaction;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.*;

/**
 * Redis Basic Operations - Temel Redis işlemleri
 * 
 * Bu sınıf Redis'in temel data structure'larını ve
 * operasyonlarını gösterir:
 * - String operations
 * - Hash operations
 * - List operations
 * - Set operations
 * - Sorted Set operations
 * - Connection pooling
 * - Pipeline operations
 * - Basic transactions
 */
public class BasicOperations {

    private static final Logger logger = LoggerFactory.getLogger(BasicOperations.class);

    // Redis connection parameters
    private static final String REDIS_HOST = "localhost";
    private static final int REDIS_PORT = 6379;
    private static final int REDIS_TIMEOUT = 3000;

    private JedisPool jedisPool;
    private ObjectMapper objectMapper;

    public BasicOperations() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        setupConnectionPool();
    }

    /**
     * Redis connection pool'unu yapılandır
     * 
     * Connection pooling avantajları:
     * - Connection reuse
     * - Thread safety
     * - Connection management
     * - Performance optimization
     */
    private void setupConnectionPool() {
        try {
            JedisPoolConfig poolConfig = new JedisPoolConfig();

            // Pool sizing
            poolConfig.setMaxTotal(20); // Maximum active connections
            poolConfig.setMaxIdle(10); // Maximum idle connections
            poolConfig.setMinIdle(2); // Minimum idle connections

            // Pool behavior
            poolConfig.setBlockWhenExhausted(true);
            poolConfig.setMaxWait(Duration.ofSeconds(5));

            // Connection validation
            poolConfig.setTestOnBorrow(true);
            poolConfig.setTestOnReturn(true);
            poolConfig.setTestWhileIdle(true);

            // Eviction policy
            poolConfig.setTimeBetweenEvictionRuns(Duration.ofSeconds(30));
            poolConfig.setMinEvictableIdleTime(Duration.ofMinutes(1));

            // Pool oluştur
            jedisPool = new JedisPool(poolConfig, REDIS_HOST, REDIS_PORT, REDIS_TIMEOUT);

            // Test connection
            try (Jedis jedis = jedisPool.getResource()) {
                String response = jedis.ping();
                logger.info("✅ Redis connection pool initialized. Ping response: {}", response);
            }

        } catch (Exception e) {
            logger.error("❌ Redis connection pool initialization failed", e);
            throw new RuntimeException("Redis connection failed", e);
        }
    }

    /**
     * String Operations - Temel key-value işlemleri
     * 
     * String Redis'te en temel data type'dır ve
     * çeşitli use case'lerde kullanılır:
     * - Simple caching
     * - Session storage
     * - Counter operations
     * - Feature flags
     */
    public void demonstrateStringOperations() {
        logger.info("🔤 String Operations demonstrasyonu başlıyor...");

        try (Jedis jedis = jedisPool.getResource()) {

            // 1. Basit SET/GET işlemleri
            String key = "user:1001:name";
            String value = "Ahmet Yılmaz";

            jedis.set(key, value);
            String retrieved = jedis.get(key);
            logger.info("SET/GET: {} = {}", key, retrieved);

            // 2. TTL (Time To Live) ile expire işlemi
            String sessionKey = "session:user1001";
            String sessionData = "{'userId':1001,'role':'admin','loginTime':'2024-01-01T10:00:00'}";

            // 1 saat expire
            jedis.setex(sessionKey, 3600, sessionData);
            Long ttl = jedis.ttl(sessionKey);
            logger.info("Session TTL: {} saniye", ttl);

            // 3. Atomic counter operations
            String counterKey = "page:views:homepage";

            // Counter'ı artır
            Long views = jedis.incr(counterKey);
            logger.info("Page views: {}", views);

            // Belirli miktarda artır
            Long newViews = jedis.incrBy(counterKey, 5);
            logger.info("Page views after +5: {}", newViews);

            // 4. Multiple operations (MSET/MGET)
            Map<String, String> userProfile = new HashMap<>();
            userProfile.put("user:1001:email", "ahmet@example.com");
            userProfile.put("user:1001:phone", "+90555123456");
            userProfile.put("user:1001:city", "Istanbul");

            // Batch set
            jedis.mset(userProfile);

            // Batch get
            List<String> userKeys = Arrays.asList("user:1001:name", "user:1001:email", "user:1001:city");
            List<String> userValues = jedis.mget(userKeys.toArray(new String[0]));

            logger.info("User profile retrieved:");
            for (int i = 0; i < userKeys.size(); i++) {
                logger.info("  {} = {}", userKeys.get(i), userValues.get(i));
            }

            // 5. Conditional operations
            String lockKey = "resource:lock:payment";

            // Set if not exists (distributed lock pattern)
            String lockResult = jedis.set(lockKey, "locked", "NX", "EX", 10);
            if ("OK".equals(lockResult)) {
                logger.info("🔒 Lock acquired: {}", lockKey);

                // Simulate critical section
                Thread.sleep(2000);

                // Release lock
                jedis.del(lockKey);
                logger.info("🔓 Lock released: {}", lockKey);
            } else {
                logger.info("❌ Could not acquire lock: {}", lockKey);
            }

        } catch (Exception e) {
            logger.error("❌ String operations error", e);
        }
    }

    /**
     * Hash Operations - Object storage için hash operations
     * 
     * Hash'ler structured data saklamak için idealdir:
     * - User profiles
     * - Product information
     * - Configuration settings
     * - Shopping carts
     */
    public void demonstrateHashOperations() {
        logger.info("🏷️ Hash Operations demonstrasyonu başlıyor...");

        try (Jedis jedis = jedisPool.getResource()) {

            String userKey = "user:1002";

            // 1. Hash field operations
            jedis.hset(userKey, "name", "Fatma Kaya");
            jedis.hset(userKey, "email", "fatma@example.com");
            jedis.hset(userKey, "age", "28");
            jedis.hset(userKey, "city", "Ankara");
            jedis.hset(userKey, "profession", "Software Engineer");

            // Single field get
            String userName = jedis.hget(userKey, "name");
            logger.info("User name: {}", userName);

            // 2. Multiple field operations
            Map<String, String> additionalFields = new HashMap<>();
            additionalFields.put("department", "Engineering");
            additionalFields.put("salary", "75000");
            additionalFields.put("startDate", "2022-03-15");

            // Batch set
            jedis.hmset(userKey, additionalFields);

            // Get all fields
            Map<String, String> allFields = jedis.hgetAll(userKey);
            logger.info("Complete user profile:");
            allFields.forEach((field, value) -> logger.info("  {}: {}", field, value));

            // 3. Hash field existence and counting
            Boolean hasEmail = jedis.hexists(userKey, "email");
            Boolean hasPhone = jedis.hexists(userKey, "phone");
            Long fieldCount = jedis.hlen(userKey);

            logger.info("Has email: {}, Has phone: {}, Total fields: {}", hasEmail, hasPhone, fieldCount);

            // 4. Hash field increment (for numeric values)
            String productKey = "product:2001:stats";

            jedis.hset(productKey, "views", "0");
            jedis.hset(productKey, "purchases", "0");
            jedis.hset(productKey, "rating_sum", "0");
            jedis.hset(productKey, "rating_count", "0");

            // Increment operations
            jedis.hincrBy(productKey, "views", 1);
            jedis.hincrBy(productKey, "views", 5);
            jedis.hincrBy(productKey, "purchases", 1);

            // Floating point increment
            jedis.hincrByFloat(productKey, "rating_sum", 4.5);
            jedis.hincrBy(productKey, "rating_count", 1);

            Map<String, String> productStats = jedis.hgetAll(productKey);
            logger.info("Product statistics:");
            productStats.forEach((stat, value) -> logger.info("  {}: {}", stat, value));

            // 5. Shopping cart example
            String cartKey = "cart:user1002";

            // Add items to cart
            jedis.hset(cartKey, "item:1001", "2"); // quantity: 2
            jedis.hset(cartKey, "item:1005", "1"); // quantity: 1
            jedis.hset(cartKey, "item:2010", "3"); // quantity: 3

            // Update quantity
            jedis.hincrBy(cartKey, "item:1001", 1); // Increase quantity

            // Get cart contents
            Map<String, String> cartItems = jedis.hgetAll(cartKey);
            logger.info("Shopping cart contents:");
            cartItems.forEach((item, quantity) -> logger.info("  {}: {} adet", item, quantity));

            // Set cart expiration (24 hours)
            jedis.expire(cartKey, 86400);

        } catch (Exception e) {
            logger.error("❌ Hash operations error", e);
        }
    }

    /**
     * List Operations - Ordered list operations
     * 
     * List'ler sıralı collections için kullanılır:
     * - Activity feeds
     * - Task queues
     * - Recent items
     * - Message queues
     */
    public void demonstrateListOperations() {
        logger.info("📝 List Operations demonstrasyonu başlıyor...");

        try (Jedis jedis = jedisPool.getResource()) {

            String listKey = "user:1001:activity_feed";

            // 1. List'e element ekleme (left/right push)
            // LPUSH - list'in başına ekle (newest first)
            jedis.lpush(listKey, createActivityMessage("login", "User logged in"));
            jedis.lpush(listKey, createActivityMessage("profile_update", "Profile updated"));
            jedis.lpush(listKey, createActivityMessage("purchase", "Purchased item #1001"));
            jedis.lpush(listKey, createActivityMessage("comment", "Commented on post #5"));
            jedis.lpush(listKey, createActivityMessage("like", "Liked post #10"));

            // 2. List length
            Long listLength = jedis.llen(listKey);
            logger.info("Activity feed length: {}", listLength);

            // 3. List elements (range operations)
            // Son 3 aktiviteyi al (most recent)
            List<String> recentActivities = jedis.lrange(listKey, 0, 2);
            logger.info("Recent 3 activities:");
            recentActivities.forEach(activity -> logger.info("  {}", activity));

            // Tüm aktiviteleri al
            List<String> allActivities = jedis.lrange(listKey, 0, -1);
            logger.info("Total activities: {}", allActivities.size());

            // 4. List manipulation
            // Index'e göre element al
            String latestActivity = jedis.lindex(listKey, 0);
            logger.info("Latest activity: {}", latestActivity);

            // Element çıkar (pop operations)
            String poppedLeft = jedis.lpop(listKey); // Son eklenen (newest)
            String poppedRight = jedis.rpop(listKey); // İlk eklenen (oldest)

            logger.info("Popped from left (newest): {}", poppedLeft);
            logger.info("Popped from right (oldest): {}", poppedRight);

            // 5. Task queue example
            String taskQueueKey = "task_queue:email";

            // Task'ları kuyruğa ekle
            jedis.rpush(taskQueueKey, createTaskMessage("send_welcome_email", "user1001"));
            jedis.rpush(taskQueueKey, createTaskMessage("send_newsletter", "all_users"));
            jedis.rpush(taskQueueKey, createTaskMessage("send_reminder", "user1005"));

            // Worker - task'ları işle
            logger.info("Processing tasks from queue:");
            String task;
            while ((task = jedis.lpop(taskQueueKey)) != null) {
                logger.info("Processing task: {}", task);
                // Simulate task processing
                Thread.sleep(500);
            }

            // 6. Capped list (fixed size list)
            String recentLoginsKey = "recent_logins";

            // Son 5 login'i tut
            for (int i = 1; i <= 10; i++) {
                jedis.lpush(recentLoginsKey, "user" + i + " - " + LocalDateTime.now());
                jedis.ltrim(recentLoginsKey, 0, 4); // Keep only last 5
            }

            List<String> recentLogins = jedis.lrange(recentLoginsKey, 0, -1);
            logger.info("Recent 5 logins:");
            recentLogins.forEach(login -> logger.info("  {}", login));

        } catch (Exception e) {
            logger.error("❌ List operations error", e);
        }
    }

    /**
     * Set Operations - Unique collections
     * 
     * Set'ler unique element collections için kullanılır:
     * - Tags
     * - Followers/Following
     * - Unique visitors
     * - Permissions
     */
    public void demonstrateSetOperations() {
        logger.info("🎯 Set Operations demonstrasyonu başlıyor...");

        try (Jedis jedis = jedisPool.getResource()) {

            // 1. Basic set operations
            String userTagsKey = "user:1001:tags";

            // Set'e element ekleme
            jedis.sadd(userTagsKey, "java", "redis", "microservices", "docker", "kubernetes");

            // Set size
            Long tagCount = jedis.scard(userTagsKey);
            logger.info("User has {} tags", tagCount);

            // Set membership test
            Boolean hasJava = jedis.sismember(userTagsKey, "java");
            Boolean hasPython = jedis.sismember(userTagsKey, "python");
            logger.info("Has Java: {}, Has Python: {}", hasJava, hasPython);

            // All members
            Set<String> allTags = jedis.smembers(userTagsKey);
            logger.info("User tags: {}", allTags);

            // 2. Set operations (union, intersection, difference)
            String user1TagsKey = "user:1001:tags";
            String user2TagsKey = "user:1002:tags";

            // User 2 tags
            jedis.sadd(user2TagsKey, "python", "redis", "mongodb", "javascript", "react");

            // Union - her iki user'ın tüm tag'leri
            Set<String> unionTags = jedis.sunion(user1TagsKey, user2TagsKey);
            logger.info("Union of tags: {}", unionTags);

            // Intersection - ortak tag'ler
            Set<String> commonTags = jedis.sinter(user1TagsKey, user2TagsKey);
            logger.info("Common tags: {}", commonTags);

            // Difference - user1'de olup user2'de olmayan
            Set<String> uniqueToUser1 = jedis.sdiff(user1TagsKey, user2TagsKey);
            logger.info("Tags unique to user1: {}", uniqueToUser1);

            // 3. Random operations
            // Random member
            String randomTag = jedis.srandmember(userTagsKey);
            logger.info("Random tag: {}", randomTag);

            // Multiple random members
            List<String> randomTags = jedis.srandmember(userTagsKey, 3);
            logger.info("3 random tags: {}", randomTags);

            // Pop random member (remove and return)
            String poppedTag = jedis.spop(userTagsKey);
            logger.info("Popped tag: {}", poppedTag);

            // 4. Followers example
            String user1FollowersKey = "user:1001:followers";
            String user1FollowingKey = "user:1001:following";

            // Add followers
            jedis.sadd(user1FollowersKey, "user1005", "user1010", "user1015", "user1020");
            jedis.sadd(user1FollowingKey, "user1002", "user1010", "user1025", "user1030");

            // Mutual followers (following each other)
            Set<String> mutualConnections = jedis.sinter(user1FollowersKey, user1FollowingKey);
            logger.info("Mutual connections: {}", mutualConnections);

            // Follower count
            Long followerCount = jedis.scard(user1FollowersKey);
            Long followingCount = jedis.scard(user1FollowingKey);
            logger.info("Followers: {}, Following: {}", followerCount, followingCount);

            // 5. Unique visitors example
            String dailyVisitorsKey = "visitors:2024-01-01";

            // Simulate visitor tracking
            String[] visitors = { "192.168.1.100", "10.0.0.1", "172.16.0.5",
                    "192.168.1.100", "203.45.67.89", "10.0.0.1" };

            for (String visitor : visitors) {
                jedis.sadd(dailyVisitorsKey, visitor);
            }

            Long uniqueVisitors = jedis.scard(dailyVisitorsKey);
            logger.info("Unique visitors today: {} (from {} total requests)",
                    uniqueVisitors, visitors.length);

        } catch (Exception e) {
            logger.error("❌ Set operations error", e);
        }
    }

    /**
     * Sorted Set Operations - Scored sorted collections
     * 
     * Sorted Set'ler score'a göre sıralanmış collections için:
     * - Leaderboards
     * - Time-based data
     * - Priority queues
     * - Rankings
     */
    public void demonstrateSortedSetOperations() {
        logger.info("🏆 Sorted Set Operations demonstrasyonu başlıyor...");

        try (Jedis jedis = jedisPool.getResource()) {

            String leaderboardKey = "game:leaderboard";

            // 1. Adding members with scores
            jedis.zadd(leaderboardKey, 1500, "player1");
            jedis.zadd(leaderboardKey, 2800, "player2");
            jedis.zadd(leaderboardKey, 2100, "player3");
            jedis.zadd(leaderboardKey, 3200, "player4");
            jedis.zadd(leaderboardKey, 1800, "player5");

            // 2. Ranking operations
            // Get rank (0-based, lowest score = 0)
            Long player1Rank = jedis.zrank(leaderboardKey, "player1");
            Long player4Rank = jedis.zrank(leaderboardKey, "player4");

            // Get reverse rank (highest score = 0)
            Long player1RevRank = jedis.zrevrank(leaderboardKey, "player1");
            Long player4RevRank = jedis.zrevrank(leaderboardKey, "player4");

            logger.info("Player1 - Rank: {}, Reverse Rank: {}", player1Rank, player1RevRank);
            logger.info("Player4 - Rank: {}, Reverse Rank: {}", player4Rank, player4RevRank);

            // 3. Score operations
            Double player2Score = jedis.zscore(leaderboardKey, "player2");
            logger.info("Player2 score: {}", player2Score);

            // Increment score
            Double newScore = jedis.zincrby(leaderboardKey, 500, "player1");
            logger.info("Player1 new score after +500: {}", newScore);

            // 4. Range operations
            // Get top 3 players (highest scores)
            List<String> topPlayers = jedis.zrevrange(leaderboardKey, 0, 2);
            logger.info("Top 3 players: {}", topPlayers);

            // Get top 3 with scores
            Map<String, Double> topPlayersWithScores = jedis.zrevrangeWithScores(leaderboardKey, 0, 2)
                    .stream()
                    .collect(java.util.stream.Collectors.toMap(
                            tuple -> tuple.getElement(),
                            tuple -> tuple.getScore(),
                            (e1, e2) -> e1,
                            LinkedHashMap::new));

            logger.info("Top 3 players with scores:");
            topPlayersWithScores.forEach((player, score) -> logger.info("  {}: {} points", player, score.intValue()));

            // 5. Score range operations
            // Players with score between 2000-3000
            List<String> midRangePlayers = jedis.zrangeByScore(leaderboardKey, 2000, 3000);
            logger.info("Players with 2000-3000 points: {}", midRangePlayers);

            // Count players in score range
            Long playersInRange = jedis.zcount(leaderboardKey, 2000, 3000);
            logger.info("Number of players with 2000-3000 points: {}", playersInRange);

            // 6. Time-based data example (activity timeline)
            String timelineKey = "user:1001:timeline";
            long currentTime = System.currentTimeMillis();

            // Add activities with timestamps as scores
            jedis.zadd(timelineKey, currentTime - 3600000, "login_event"); // 1 hour ago
            jedis.zadd(timelineKey, currentTime - 1800000, "profile_update"); // 30 min ago
            jedis.zadd(timelineKey, currentTime - 900000, "post_created"); // 15 min ago
            jedis.zadd(timelineKey, currentTime - 300000, "comment_posted"); // 5 min ago
            jedis.zadd(timelineKey, currentTime, "page_viewed"); // now

            // Get recent activities (last 45 minutes)
            long fortyFiveMinutesAgo = currentTime - 2700000;
            List<String> recentActivities = jedis.zrangeByScore(timelineKey,
                    fortyFiveMinutesAgo,
                    currentTime);
            logger.info("Activities in last 45 minutes: {}", recentActivities);

            // 7. Priority queue example
            String priorityQueueKey = "tasks:priority_queue";

            // Add tasks with priority scores (higher = more important)
            jedis.zadd(priorityQueueKey, 1, "backup_database");
            jedis.zadd(priorityQueueKey, 5, "critical_bug_fix");
            jedis.zadd(priorityQueueKey, 3, "deploy_feature");
            jedis.zadd(priorityQueueKey, 4, "security_update");
            jedis.zadd(priorityQueueKey, 2, "clean_logs");

            // Process tasks by priority (highest first)
            logger.info("Processing tasks by priority:");
            while (jedis.zcard(priorityQueueKey) > 0) {
                // Get highest priority task
                List<String> highestPriorityTask = jedis.zrevrange(priorityQueueKey, 0, 0);
                if (!highestPriorityTask.isEmpty()) {
                    String task = highestPriorityTask.get(0);
                    Double priority = jedis.zscore(priorityQueueKey, task);

                    logger.info("  Processing: {} (priority: {})", task, priority.intValue());

                    // Remove from queue
                    jedis.zrem(priorityQueueKey, task);

                    // Simulate processing
                    Thread.sleep(200);
                }
            }

        } catch (Exception e) {
            logger.error("❌ Sorted set operations error", e);
        }
    }

    /**
     * Pipeline Operations - Batch operations for performance
     * 
     * Pipeline Redis'e multiple commands'ı tek round-trip'te gönderir:
     * - Reduced network latency
     * - Higher throughput
     * - Batch processing
     */
    public void demonstratePipelineOperations() {
        logger.info("🚀 Pipeline Operations demonstrasyonu başlıyor...");

        try (Jedis jedis = jedisPool.getResource()) {

            // 1. Normal operations vs Pipeline comparison
            long startTime = System.currentTimeMillis();

            // Normal operations (individual round-trips)
            for (int i = 0; i < 100; i++) {
                jedis.set("normal:key:" + i, "value" + i);
            }

            long normalTime = System.currentTimeMillis() - startTime;

            // Pipeline operations (batched)
            startTime = System.currentTimeMillis();

            Pipeline pipeline = jedis.pipelined();
            for (int i = 0; i < 100; i++) {
                pipeline.set("pipeline:key:" + i, "value" + i);
            }
            pipeline.sync(); // Execute all commands

            long pipelineTime = System.currentTimeMillis() - startTime;

            logger.info("Performance comparison:");
            logger.info("  Normal operations: {} ms", normalTime);
            logger.info("  Pipeline operations: {} ms", pipelineTime);
            logger.info("  Pipeline improvement: {}x faster",
                    String.format("%.2f", (double) normalTime / pipelineTime));

            // 2. Pipeline with responses
            Pipeline responsePipeline = jedis.pipelined();

            // Queue multiple operations
            Response<String> setResponse = responsePipeline.set("pipeline:test", "test_value");
            Response<String> getResponse = responsePipeline.get("pipeline:test");
            Response<Long> incrResponse = responsePipeline.incr("pipeline:counter");
            Response<Boolean> existsResponse = responsePipeline.exists("pipeline:test");

            // Execute pipeline
            responsePipeline.sync();

            // Get responses
            logger.info("Pipeline responses:");
            logger.info("  SET result: {}", setResponse.get());
            logger.info("  GET result: {}", getResponse.get());
            logger.info("  INCR result: {}", incrResponse.get());
            logger.info("  EXISTS result: {}", existsResponse.get());

            // 3. Complex pipeline example - User session batch update
            String userId = "user:2001";
            Pipeline sessionPipeline = jedis.pipelined();

            // Session data update
            sessionPipeline.hset(userId + ":profile", "lastLogin", LocalDateTime.now().toString());
            sessionPipeline.hset(userId + ":profile", "loginCount", "1");
            sessionPipeline.hincrBy(userId + ":profile", "loginCount", 1);
            sessionPipeline.sadd(userId + ":devices", "mobile-iphone");
            sessionPipeline.lpush(userId + ":activity", "login:" + System.currentTimeMillis());
            sessionPipeline.expire(userId + ":session", 3600); // 1 hour session

            // Analytics update
            sessionPipeline.incr("analytics:daily_logins:2024-01-01");
            sessionPipeline.sadd("analytics:active_users:2024-01-01", userId);
            sessionPipeline.zincrby("analytics:user_activity", 1, userId);

            // Execute batch
            sessionPipeline.sync();

            logger.info("✅ User session batch update completed for {}", userId);

            // 4. Error handling in pipeline
            try {
                Pipeline errorPipeline = jedis.pipelined();

                // Valid operations
                errorPipeline.set("valid:key1", "value1");
                errorPipeline.set("valid:key2", "value2");

                // Invalid operation (will cause error)
                errorPipeline.lpush("valid:key1", "this will fail"); // key1 is string, not list

                errorPipeline.set("valid:key3", "value3");

                // Execute - some operations will fail
                errorPipeline.sync();

            } catch (Exception e) {
                logger.warn("⚠️ Pipeline had some errors (expected): {}", e.getMessage());
            }

        } catch (Exception e) {
            logger.error("❌ Pipeline operations error", e);
        }
    }

    /**
     * Transaction Operations - ACID transactions with MULTI/EXEC
     * 
     * Redis transactions provide:
     * - Atomic execution
     * - Isolation during execution
     * - Optimistic locking with WATCH
     */
    public void demonstrateTransactionOperations() {
        logger.info("🔒 Transaction Operations demonstrasyonu başlıyor...");

        try (Jedis jedis = jedisPool.getResource()) {

            // 1. Basic transaction example
            String accountKey = "account:1001:balance";
            jedis.set(accountKey, "1000"); // Initial balance

            // Transaction to update balance
            Transaction transaction = jedis.multi();
            transaction.decrBy(accountKey, 100); // Withdraw 100
            transaction.lpush("account:1001:transactions", "withdrawal:100:" + System.currentTimeMillis());

            // Execute transaction
            List<Object> results = transaction.exec();
            logger.info("Transaction results: {}", results);

            String newBalance = jedis.get(accountKey);
            logger.info("New balance after withdrawal: {}", newBalance);

            // 2. Optimistic locking with WATCH
            String inventoryKey = "product:1001:stock";
            jedis.set(inventoryKey, "10"); // Initial stock

            // Simulate concurrent stock update
            new Thread(() -> {
                try (Jedis concurrentJedis = jedisPool.getResource()) {
                    Thread.sleep(1000); // Wait a bit
                    concurrentJedis.decrBy(inventoryKey, 2); // Another process reduces stock
                    logger.info("🔄 Concurrent update: reduced stock by 2");
                } catch (Exception e) {
                    logger.error("Concurrent update error", e);
                }
            }).start();

            // Watch the inventory key
            jedis.watch(inventoryKey);

            // Get current stock
            String currentStock = jedis.get(inventoryKey);
            int stock = Integer.parseInt(currentStock);

            logger.info("Current stock: {}", stock);

            // Try to reduce stock if available
            if (stock >= 5) {
                Thread.sleep(1500); // Simulate processing delay

                // Start transaction
                Transaction stockTransaction = jedis.multi();
                stockTransaction.decrBy(inventoryKey, 5);
                stockTransaction.lpush("product:1001:orders", "order:5_units:" + System.currentTimeMillis());

                // Execute - might fail if stock was modified
                List<Object> stockResults = stockTransaction.exec();

                if (stockResults == null) {
                    logger.warn("⚠️ Transaction failed due to concurrent modification (WATCH detected change)");
                } else {
                    logger.info("✅ Stock transaction successful: {}", stockResults);
                }
            } else {
                jedis.unwatch(); // Cancel watch
                logger.warn("❌ Insufficient stock for transaction");
            }

            // 3. Complex business transaction example
            transferMoney("account:1001", "account:1002", 250);

        } catch (Exception e) {
            logger.error("❌ Transaction operations error", e);
        }
    }

    /**
     * Money transfer with transaction
     */
    private void transferMoney(String fromAccount, String toAccount, int amount) {
        try (Jedis jedis = jedisPool.getResource()) {

            // Initialize accounts if not exist
            if (!jedis.exists(fromAccount + ":balance")) {
                jedis.set(fromAccount + ":balance", "1000");
            }
            if (!jedis.exists(toAccount + ":balance")) {
                jedis.set(toAccount + ":balance", "500");
            }

            // Watch both accounts
            jedis.watch(fromAccount + ":balance", toAccount + ":balance");

            // Check balances
            String fromBalanceStr = jedis.get(fromAccount + ":balance");
            String toBalanceStr = jedis.get(toAccount + ":balance");

            int fromBalance = Integer.parseInt(fromBalanceStr);
            int toBalance = Integer.parseInt(toBalanceStr);

            logger.info("Transfer attempt: {} -> {} (amount: {})", fromAccount, toAccount, amount);
            logger.info("From balance: {}, To balance: {}", fromBalance, toBalance);

            if (fromBalance >= amount) {
                // Start transaction
                Transaction transferTransaction = jedis.multi();

                // Update balances
                transferTransaction.decrBy(fromAccount + ":balance", amount);
                transferTransaction.incrBy(toAccount + ":balance", amount);

                // Add transaction records
                String transferId = "transfer:" + System.currentTimeMillis();
                transferTransaction.lpush(fromAccount + ":transactions",
                        String.format("transfer_out:%d:%s:%s", amount, toAccount, transferId));
                transferTransaction.lpush(toAccount + ":transactions",
                        String.format("transfer_in:%d:%s:%s", amount, fromAccount, transferId));

                // Execute transfer
                List<Object> transferResults = transferTransaction.exec();

                if (transferResults == null) {
                    logger.warn("⚠️ Transfer failed due to concurrent modification");
                } else {
                    logger.info("✅ Transfer successful: {} -> {} (amount: {})", fromAccount, toAccount, amount);

                    // Verify new balances
                    String newFromBalance = jedis.get(fromAccount + ":balance");
                    String newToBalance = jedis.get(toAccount + ":balance");
                    logger.info("New balances - From: {}, To: {}", newFromBalance, newToBalance);
                }
            } else {
                jedis.unwatch();
                logger.warn("❌ Insufficient funds for transfer");
            }

        } catch (Exception e) {
            logger.error("❌ Money transfer error", e);
        }
    }

    /**
     * Helper method - Create activity message
     */
    private String createActivityMessage(String type, String description) {
        try {
            Map<String, Object> activity = new HashMap<>();
            activity.put("type", type);
            activity.put("description", description);
            activity.put("timestamp", LocalDateTime.now().toString());
            activity.put("userId", "1001");

            return objectMapper.writeValueAsString(activity);
        } catch (Exception e) {
            return String.format("{\"type\":\"%s\",\"description\":\"%s\"}", type, description);
        }
    }

    /**
     * Helper method - Create task message
     */
    private String createTaskMessage(String taskType, String target) {
        try {
            Map<String, Object> task = new HashMap<>();
            task.put("taskType", taskType);
            task.put("target", target);
            task.put("createdAt", LocalDateTime.now().toString());
            task.put("status", "pending");

            return objectMapper.writeValueAsString(task);
        } catch (Exception e) {
            return String.format("{\"taskType\":\"%s\",\"target\":\"%s\"}", taskType, target);
        }
    }

    /**
     * Resource cleanup
     */
    public void close() {
        if (jedisPool != null && !jedisPool.isClosed()) {
            jedisPool.close();
            logger.info("🔒 Redis connection pool closed");
        }
    }

    /**
     * Demo runner
     */
    public void runAllDemonstrations() {
        logger.info("🚀 Redis Basic Operations Demo başlıyor...");

        try {
            demonstrateStringOperations();
            Thread.sleep(1000);

            demonstrateHashOperations();
            Thread.sleep(1000);

            demonstrateListOperations();
            Thread.sleep(1000);

            demonstrateSetOperations();
            Thread.sleep(1000);

            demonstrateSortedSetOperations();
            Thread.sleep(1000);

            demonstratePipelineOperations();
            Thread.sleep(1000);

            demonstrateTransactionOperations();

            logger.info("✅ Tüm Redis operasyonları tamamlandı!");

        } catch (Exception e) {
            logger.error("❌ Demo execution error", e);
        }
    }

    /**
     * Main method
     */
    public static void main(String[] args) {
        BasicOperations demo = new BasicOperations();

        try {
            demo.runAllDemonstrations();
        } finally {
            demo.close();
        }
    }
}