package com.example.redis;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;
import redis.clients.jedis.JedisPubSub;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Redis Pub/Sub Example - Real-time Messaging
 * 
 * Bu sınıf Redis Pub/Sub mekanizmasını gösterir:
 * - Publisher/Subscriber pattern
 * - Pattern-based subscriptions
 * - Real-time chat application
 * - Event-driven messaging
 * - Multi-channel subscriptions
 */
public class PubSubExample {

    private static final Logger logger = LoggerFactory.getLogger(PubSubExample.class);

    // Redis connection parameters
    private static final String REDIS_HOST = "localhost";
    private static final int REDIS_PORT = 6379;
    private static final int REDIS_TIMEOUT = 3000;

    private JedisPool jedisPool;
    private ObjectMapper objectMapper;
    private ExecutorService executorService;
    private AtomicBoolean isRunning = new AtomicBoolean(false);

    public PubSubExample() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        this.executorService = Executors.newCachedThreadPool();
        setupConnectionPool();
    }

    /**
     * Redis connection pool'unu yapılandır
     */
    private void setupConnectionPool() {
        try {
            JedisPoolConfig poolConfig = new JedisPoolConfig();
            poolConfig.setMaxTotal(20);
            poolConfig.setMaxIdle(10);
            poolConfig.setMinIdle(2);
            poolConfig.setBlockWhenExhausted(true);
            poolConfig.setMaxWait(Duration.ofSeconds(5));
            poolConfig.setTestOnBorrow(true);

            jedisPool = new JedisPool(poolConfig, REDIS_HOST, REDIS_PORT, REDIS_TIMEOUT);

            // Test connection
            try (Jedis jedis = jedisPool.getResource()) {
                String response = jedis.ping();
                logger.info("✅ Redis Pub/Sub connection established. Ping: {}", response);
            }

        } catch (Exception e) {
            logger.error("❌ Redis connection failed", e);
            throw new RuntimeException("Redis connection failed", e);
        }
    }

    /**
     * Simple Publisher - Belirli channel'a mesaj gönder
     */
    public void publishMessage(String channel, String message) {
        try (Jedis jedis = jedisPool.getResource()) {

            // Mesaj verilerini hazırla
            Map<String, Object> messageData = new HashMap<>();
            messageData.put("content", message);
            messageData.put("timestamp", LocalDateTime.now().toString());
            messageData.put("channel", channel);
            messageData.put("messageId", UUID.randomUUID().toString());

            String jsonMessage = objectMapper.writeValueAsString(messageData);

            // Mesajı publish et
            Long subscriberCount = jedis.publish(channel, jsonMessage);

            logger.info("📤 Published to '{}': '{}' (reached {} subscribers)",
                    channel, message, subscriberCount);

        } catch (Exception e) {
            logger.error("❌ Failed to publish message", e);
        }
    }

    /**
     * Chat Publisher - Chat mesajları gönder
     */
    public void publishChatMessage(String room, String username, String message) {
        try (Jedis jedis = jedisPool.getResource()) {

            String channel = "chat:room:" + room;

            Map<String, Object> chatMessage = new HashMap<>();
            chatMessage.put("type", "chat_message");
            chatMessage.put("room", room);
            chatMessage.put("username", username);
            chatMessage.put("message", message);
            chatMessage.put("timestamp", LocalDateTime.now().toString());
            chatMessage.put("messageId", UUID.randomUUID().toString());

            String jsonMessage = objectMapper.writeValueAsString(chatMessage);
            Long subscriberCount = jedis.publish(channel, jsonMessage);

            logger.info("💬 [{}] {}  says: '{}' (delivered to {} users)",
                    room, username, message, subscriberCount);

        } catch (Exception e) {
            logger.error("❌ Failed to publish chat message", e);
        }
    }

    /**
     * System Event Publisher - Sistem olaylarını publish et
     */
    public void publishSystemEvent(String eventType, Map<String, Object> eventData) {
        try (Jedis jedis = jedisPool.getResource()) {

            String channel = "system:events:" + eventType;

            Map<String, Object> systemEvent = new HashMap<>();
            systemEvent.put("type", "system_event");
            systemEvent.put("eventType", eventType);
            systemEvent.put("data", eventData);
            systemEvent.put("timestamp", LocalDateTime.now().toString());
            systemEvent.put("eventId", UUID.randomUUID().toString());

            String jsonMessage = objectMapper.writeValueAsString(systemEvent);
            Long subscriberCount = jedis.publish(channel, jsonMessage);

            logger.info("🔔 System event '{}' published (reached {} subscribers)",
                    eventType, subscriberCount);

        } catch (Exception e) {
            logger.error("❌ Failed to publish system event", e);
        }
    }

    /**
     * Simple Subscriber - Belirli channel'ı dinle
     */
    public CompletableFuture<Void> subscribeToChannel(String channel, String subscriberName) {
        return CompletableFuture.runAsync(() -> {
            try (Jedis jedis = jedisPool.getResource()) {

                logger.info("👂 [{}] Subscribing to channel: {}", subscriberName, channel);

                JedisPubSub pubSub = new JedisPubSub() {
                    @Override
                    public void onMessage(String channel, String message) {
                        try {
                            @SuppressWarnings("unchecked")
                            Map<String, Object> messageData = objectMapper.readValue(message, Map.class);

                            String content = (String) messageData.get("content");
                            String timestamp = (String) messageData.get("timestamp");

                            logger.info("📨 [{}] Received from '{}': {}",
                                    subscriberName, channel, content);

                        } catch (Exception e) {
                            logger.error("❌ Error processing message", e);
                        }
                    }

                    @Override
                    public void onSubscribe(String channel, int subscribedChannels) {
                        logger.info("✅ [{}] Subscribed to '{}' (total: {} channels)",
                                subscriberName, channel, subscribedChannels);
                    }

                    @Override
                    public void onUnsubscribe(String channel, int subscribedChannels) {
                        logger.info("❌ [{}] Unsubscribed from '{}' (remaining: {} channels)",
                                subscriberName, channel, subscribedChannels);
                    }
                };

                // Subscribe - blocking operation
                jedis.subscribe(pubSub, channel);

            } catch (Exception e) {
                logger.error("❌ [{}] Subscription error", subscriberName, e);
            }
        }, executorService);
    }

    /**
     * Pattern Subscriber - Pattern-based subscription
     */
    public CompletableFuture<Void> subscribeToPattern(String pattern, String subscriberName) {
        return CompletableFuture.runAsync(() -> {
            try (Jedis jedis = jedisPool.getResource()) {

                logger.info("👂 [{}] Subscribing to pattern: {}", subscriberName, pattern);

                JedisPubSub pubSub = new JedisPubSub() {
                    @Override
                    public void onPMessage(String pattern, String channel, String message) {
                        try {
                            @SuppressWarnings("unchecked")
                            Map<String, Object> messageData = objectMapper.readValue(message, Map.class);

                            String type = (String) messageData.get("type");
                            String timestamp = (String) messageData.get("timestamp");

                            if ("chat_message".equals(type)) {
                                handleChatMessage(subscriberName, channel, messageData);
                            } else if ("system_event".equals(type)) {
                                handleSystemEvent(subscriberName, channel, messageData);
                            } else {
                                logger.info("📨 [{}] Received from '{}': {}",
                                        subscriberName, channel, messageData.get("content"));
                            }

                        } catch (Exception e) {
                            logger.error("❌ Error processing pattern message", e);
                        }
                    }

                    @Override
                    public void onPSubscribe(String pattern, int subscribedChannels) {
                        logger.info("✅ [{}] Subscribed to pattern '{}' (total: {} patterns)",
                                subscriberName, pattern, subscribedChannels);
                    }

                    @Override
                    public void onPUnsubscribe(String pattern, int subscribedChannels) {
                        logger.info("❌ [{}] Unsubscribed from pattern '{}' (remaining: {} patterns)",
                                subscriberName, pattern, subscribedChannels);
                    }
                };

                // Pattern subscribe - blocking operation
                jedis.psubscribe(pubSub, pattern);

            } catch (Exception e) {
                logger.error("❌ [{}] Pattern subscription error", subscriberName, e);
            }
        }, executorService);
    }

    /**
     * Chat message handler
     */
    private void handleChatMessage(String subscriberName, String channel, Map<String, Object> messageData) {
        String room = (String) messageData.get("room");
        String username = (String) messageData.get("username");
        String message = (String) messageData.get("message");
        String timestamp = (String) messageData.get("timestamp");

        String shortTime = timestamp.substring(11, 19); // HH:mm:ss format
        System.out.printf("💬 [%s] %s (%s): %s%n", room, username, shortTime, message);
    }

    /**
     * System event handler
     */
    private void handleSystemEvent(String subscriberName, String channel, Map<String, Object> messageData) {
        String eventType = (String) messageData.get("eventType");
        @SuppressWarnings("unchecked")
        Map<String, Object> eventData = (Map<String, Object>) messageData.get("data");
        String timestamp = (String) messageData.get("timestamp");

        String shortTime = timestamp.substring(11, 19);
        logger.info("🔔 [{}] System Event '{}' at {}: {}",
                subscriberName, eventType, shortTime, eventData);
    }

    /**
     * Multi-Channel Subscriber - Birden fazla channel'ı dinle
     */
    public CompletableFuture<Void> subscribeToMultipleChannels(String[] channels, String subscriberName) {
        return CompletableFuture.runAsync(() -> {
            try (Jedis jedis = jedisPool.getResource()) {

                logger.info("👂 [{}] Subscribing to {} channels: {}",
                        subscriberName, channels.length, Arrays.toString(channels));

                JedisPubSub pubSub = new JedisPubSub() {
                    @Override
                    public void onMessage(String channel, String message) {
                        try {
                            @SuppressWarnings("unchecked")
                            Map<String, Object> messageData = objectMapper.readValue(message, Map.class);

                            String content = (String) messageData.get("content");
                            String timestamp = (String) messageData.get("timestamp");
                            String shortTime = timestamp.substring(11, 19);

                            logger.info("📨 [{}] {} ({}): {}",
                                    subscriberName, channel, shortTime, content);

                        } catch (Exception e) {
                            logger.error("❌ Error processing multi-channel message", e);
                        }
                    }

                    @Override
                    public void onSubscribe(String channel, int subscribedChannels) {
                        logger.info("✅ [{}] Subscribed to '{}' ({}/{} channels)",
                                subscriberName, channel, subscribedChannels, channels.length);
                    }
                };

                // Subscribe to multiple channels
                jedis.subscribe(pubSub, channels);

            } catch (Exception e) {
                logger.error("❌ [{}] Multi-channel subscription error", subscriberName, e);
            }
        }, executorService);
    }

    /**
     * Batch message publisher
     */
    public void publishBatchMessages(String channel, String prefix, int count) {
        logger.info("📦 Publishing batch messages to '{}': {} messages", channel, count);

        long startTime = System.currentTimeMillis();

        for (int i = 1; i <= count; i++) {
            String message = String.format("%s - Message #%d", prefix, i);
            publishMessage(channel, message);

            // Rate limiting
            if (i % 10 == 0) {
                try {
                    Thread.sleep(100); // 100ms pause every 10 messages
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }

        long duration = System.currentTimeMillis() - startTime;
        double messagesPerSecond = (count * 1000.0) / duration;

        logger.info("✅ Batch published: {} messages in {} ms ({:.2f} msg/sec)",
                count, duration, messagesPerSecond);
    }

    /**
     * Real-time Chat Demo
     */
    public void runChatDemo() {
        logger.info("🚀 Starting Redis Pub/Sub Chat Demo...");

        try {
            isRunning.set(true);

            // Start chat room subscribers
            CompletableFuture<Void> generalRoomSub = subscribeToPattern("chat:room:general", "GeneralListener");
            CompletableFuture<Void> techRoomSub = subscribeToPattern("chat:room:tech", "TechListener");
            CompletableFuture<Void> allRoomsSub = subscribeToPattern("chat:room:*", "AllRoomsListener");

            // Start system event subscriber
            CompletableFuture<Void> systemSub = subscribeToPattern("system:events:*", "SystemListener");

            // Wait for subscribers to initialize
            Thread.sleep(2000);

            // Simulate chat activity
            publishChatMessage("general", "Alice", "Hello everyone!");
            Thread.sleep(500);

            publishChatMessage("tech", "Bob", "Anyone familiar with Redis Pub/Sub?");
            Thread.sleep(500);

            publishChatMessage("general", "Charlie", "Great weather today!");
            Thread.sleep(500);

            // Simulate system events
            Map<String, Object> userJoinEvent = new HashMap<>();
            userJoinEvent.put("userId", "user123");
            userJoinEvent.put("username", "Alice");
            userJoinEvent.put("action", "joined");
            publishSystemEvent("user_activity", userJoinEvent);

            Thread.sleep(500);

            Map<String, Object> serverEvent = new HashMap<>();
            serverEvent.put("server", "redis-01");
            serverEvent.put("status", "healthy");
            serverEvent.put("memory_usage", "45%");
            publishSystemEvent("server_status", serverEvent);

            // Keep demo running
            logger.info("💬 Chat demo running... Press Ctrl+C to stop");
            Thread.sleep(5000);

            // Send some more messages
            publishChatMessage("tech", "Alice", "Redis Pub/Sub is really fast!");
            publishChatMessage("general", "Bob", "Anyone want to grab coffee?");

            Thread.sleep(3000);

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            logger.info("⚠️ Chat demo interrupted");
        } catch (Exception e) {
            logger.error("❌ Chat demo error", e);
        } finally {
            isRunning.set(false);
        }
    }

    /**
     * Performance test
     */
    public void runPerformanceTest() {
        logger.info("🏃 Starting Redis Pub/Sub Performance Test...");

        try {
            String testChannel = "performance:test";

            // Start a subscriber
            CompletableFuture<Void> subscriber = subscribeToChannel(testChannel, "PerformanceListener");

            Thread.sleep(1000); // Wait for subscriber to connect

            // Performance test with different batch sizes
            int[] batchSizes = { 10, 50, 100, 500, 1000 };

            for (int batchSize : batchSizes) {
                logger.info("📊 Testing batch size: {}", batchSize);
                publishBatchMessages(testChannel, "PerfTest", batchSize);
                Thread.sleep(2000); // Cool down between tests
            }

        } catch (Exception e) {
            logger.error("❌ Performance test error", e);
        }
    }

    /**
     * Resource cleanup
     */
    public void close() {
        isRunning.set(false);

        if (executorService != null && !executorService.isShutdown()) {
            executorService.shutdown();
            logger.info("🛑 Executor service shut down");
        }

        if (jedisPool != null && !jedisPool.isClosed()) {
            jedisPool.close();
            logger.info("🔒 Redis connection pool closed");
        }
    }

    /**
     * Graceful shutdown hook
     */
    private void setupShutdownHook() {
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info("🛑 Graceful shutdown initiated...");
            close();
            logger.info("✅ Graceful shutdown completed");
        }));
    }

    /**
     * Main method - Demo selector
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java PubSubExample <mode>");
            System.out.println("Modes:");
            System.out.println("  chat        - Real-time chat demo");
            System.out.println("  performance - Performance test");
            System.out.println("  simple      - Simple pub/sub demo");
            return;
        }

        String mode = args[0].toLowerCase();
        PubSubExample pubSubExample = new PubSubExample();
        pubSubExample.setupShutdownHook();

        try {
            switch (mode) {
                case "chat":
                    pubSubExample.runChatDemo();
                    break;

                case "performance":
                    pubSubExample.runPerformanceTest();
                    break;

                case "simple":
                    pubSubExample.runSimpleDemo();
                    break;

                default:
                    logger.error("❌ Unknown mode: {}", mode);
                    return;
            }

            // Keep application running
            Thread.sleep(Long.MAX_VALUE);

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            logger.info("⚠️ Application interrupted");
        } catch (Exception e) {
            logger.error("❌ Application error", e);
        } finally {
            pubSubExample.close();
        }
    }

    /**
     * Simple demo
     */
    private void runSimpleDemo() {
        logger.info("🚀 Starting Simple Pub/Sub Demo...");

        try {
            String[] channels = { "news", "alerts", "notifications" };

            // Start subscribers
            CompletableFuture<Void> newsSubscriber = subscribeToChannel("news", "NewsReader");
            CompletableFuture<Void> alertSubscriber = subscribeToChannel("alerts", "AlertMonitor");
            CompletableFuture<Void> multiSubscriber = subscribeToMultipleChannels(channels, "MultiListener");

            Thread.sleep(2000); // Wait for subscribers

            // Publish some messages
            publishMessage("news", "Breaking: Redis 8.0 released!");
            Thread.sleep(500);

            publishMessage("alerts", "High CPU usage detected on server-01");
            Thread.sleep(500);

            publishMessage("notifications", "New user registered: user123");
            Thread.sleep(500);

            publishMessage("news", "Tech conference announced for next month");

            logger.info("✅ Simple demo completed");
            Thread.sleep(3000);

        } catch (Exception e) {
            logger.error("❌ Simple demo error", e);
        }
    }
}