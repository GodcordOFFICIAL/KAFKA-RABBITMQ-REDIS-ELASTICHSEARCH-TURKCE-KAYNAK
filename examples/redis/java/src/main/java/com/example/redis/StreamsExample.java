package com.example.redis;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;
import redis.clients.jedis.StreamEntry;
import redis.clients.jedis.StreamEntryID;
import redis.clients.jedis.params.XAddParams;
import redis.clients.jedis.params.XReadGroupParams;
import redis.clients.jedis.params.XReadParams;

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
 * Redis Streams Example - Event Streaming ve Consumer Groups
 * 
 * Bu sınıf Redis Streams'in gelişmiş özelliklerini gösterir:
 * - Event streaming
 * - Consumer groups
 * - Message acknowledgment
 * - Stream trimming
 * - Pending messages handling
 * - Real-time event processing
 */
public class StreamsExample {

    private static final Logger logger = LoggerFactory.getLogger(StreamsExample.class);

    // Redis connection parameters
    private static final String REDIS_HOST = "localhost";
    private static final int REDIS_PORT = 6379;
    private static final int REDIS_TIMEOUT = 3000;

    private JedisPool jedisPool;
    private ObjectMapper objectMapper;
    private ExecutorService executorService;
    private AtomicBoolean isRunning = new AtomicBoolean(false);

    public StreamsExample() {
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
                logger.info("✅ Redis Streams connection established. Ping: {}", response);
            }

        } catch (Exception e) {
            logger.error("❌ Redis connection failed", e);
            throw new RuntimeException("Redis connection failed", e);
        }
    }

    /**
     * Stream'e event ekle
     */
    public String addEvent(String streamKey, Map<String, String> eventData) {
        try (Jedis jedis = jedisPool.getResource()) {

            // Event metadata'sı ekle
            Map<String, String> fullEventData = new HashMap<>(eventData);
            fullEventData.put("timestamp", LocalDateTime.now().toString());
            fullEventData.put("event_id", UUID.randomUUID().toString());

            // Stream'e ekle - Redis otomatik ID oluşturur (*)
            StreamEntryID entryId = jedis.xadd(streamKey, StreamEntryID.NEW_ENTRY, fullEventData);

            logger.info("📝 Event added to stream '{}': {} (ID: {})",
                    streamKey, eventData, entryId);

            return entryId.toString();

        } catch (Exception e) {
            logger.error("❌ Failed to add event to stream", e);
            return null;
        }
    }

    /**
     * Stream'e event ekle (custom ID ile)
     */
    public String addEventWithCustomId(String streamKey, String customId, Map<String, String> eventData) {
        try (Jedis jedis = jedisPool.getResource()) {

            Map<String, String> fullEventData = new HashMap<>(eventData);
            fullEventData.put("timestamp", LocalDateTime.now().toString());

            // Custom ID ile ekle
            StreamEntryID entryId = jedis.xadd(streamKey, new StreamEntryID(customId), fullEventData);

            logger.info("📝 Event added with custom ID to '{}': {} (ID: {})",
                    streamKey, eventData, entryId);

            return entryId.toString();

        } catch (Exception e) {
            logger.error("❌ Failed to add event with custom ID", e);
            return null;
        }
    }

    /**
     * Stream'den event'leri oku (basit okuma)
     */
    public List<StreamEntry> readEvents(String streamKey, String startId, int count) {
        try (Jedis jedis = jedisPool.getResource()) {

            StreamEntryID start = startId.equals("0") ? StreamEntryID.MINIMUM : new StreamEntryID(startId);

            // Stream'den oku
            List<StreamEntry> entries = jedis.xread(
                    XReadParams.xReadParams().count(count),
                    Collections.singletonMap(streamKey, start)).get(streamKey);

            logger.info("📖 Read {} events from stream '{}'", entries.size(), streamKey);

            return entries;

        } catch (Exception e) {
            logger.error("❌ Failed to read events from stream", e);
            return Collections.emptyList();
        }
    }

    /**
     * Consumer group oluştur
     */
    public boolean createConsumerGroup(String streamKey, String groupName, String startId) {
        try (Jedis jedis = jedisPool.getResource()) {

            StreamEntryID start = startId.equals("0") ? StreamEntryID.MINIMUM
                    : startId.equals("$") ? StreamEntryID.MAXIMUM : new StreamEntryID(startId);

            // Consumer group oluştur
            String result = jedis.xgroupCreate(streamKey, groupName, start, false);

            logger.info("✅ Consumer group '{}' created for stream '{}' (result: {})",
                    groupName, streamKey, result);

            return "OK".equals(result);

        } catch (Exception e) {
            if (e.getMessage().contains("BUSYGROUP")) {
                logger.info("ℹ️ Consumer group '{}' already exists for stream '{}'", groupName, streamKey);
                return true;
            } else {
                logger.error("❌ Failed to create consumer group", e);
                return false;
            }
        }
    }

    /**
     * Consumer group ile event'leri oku
     */
    public List<StreamEntry> readFromConsumerGroup(String streamKey, String groupName,
            String consumerName, int count) {
        try (Jedis jedis = jedisPool.getResource()) {

            // Consumer group'tan oku
            Map<String, List<StreamEntry>> result = jedis.xreadGroup(
                    groupName,
                    consumerName,
                    XReadGroupParams.xReadGroupParams().count(count),
                    Collections.singletonMap(streamKey, StreamEntryID.UNRECEIVED_ENTRY));

            List<StreamEntry> entries = result.getOrDefault(streamKey, Collections.emptyList());

            logger.info("📖 [{}:{}] Read {} events from stream '{}'",
                    groupName, consumerName, entries.size(), streamKey);

            return entries;

        } catch (Exception e) {
            logger.error("❌ Failed to read from consumer group", e);
            return Collections.emptyList();
        }
    }

    /**
     * Consumer group ile blocking read
     */
    public CompletableFuture<Void> blockingReadFromConsumerGroup(String streamKey, String groupName,
            String consumerName, int blockTimeMs) {
        return CompletableFuture.runAsync(() -> {
            try (Jedis jedis = jedisPool.getResource()) {

                logger.info("👂 [{}:{}] Starting blocking read from stream '{}'",
                        groupName, consumerName, streamKey);

                while (isRunning.get()) {
                    try {
                        // Blocking read with timeout
                        Map<String, List<StreamEntry>> result = jedis.xreadGroup(
                                groupName,
                                consumerName,
                                XReadGroupParams.xReadGroupParams().count(10).block(blockTimeMs),
                                Collections.singletonMap(streamKey, StreamEntryID.UNRECEIVED_ENTRY));

                        List<StreamEntry> entries = result.getOrDefault(streamKey, Collections.emptyList());

                        for (StreamEntry entry : entries) {
                            processStreamEntry(streamKey, groupName, consumerName, entry);

                            // Message'ı acknowledge et
                            acknowledgeMessage(streamKey, groupName, entry.getID());
                        }

                    } catch (Exception e) {
                        if (isRunning.get()) {
                            logger.error("❌ Error in blocking read", e);
                            Thread.sleep(1000); // Error recovery delay
                        }
                    }
                }

                logger.info("🛑 [{}:{}] Stopped blocking read", groupName, consumerName);

            } catch (Exception e) {
                logger.error("❌ Consumer group reader error", e);
            }
        }, executorService);
    }

    /**
     * Message'ı acknowledge et
     */
    public boolean acknowledgeMessage(String streamKey, String groupName, StreamEntryID messageId) {
        try (Jedis jedis = jedisPool.getResource()) {

            Long result = jedis.xack(streamKey, groupName, messageId);

            logger.debug("✅ Acknowledged message {} in group '{}' (result: {})",
                    messageId, groupName, result);

            return result > 0;

        } catch (Exception e) {
            logger.error("❌ Failed to acknowledge message", e);
            return false;
        }
    }

    /**
     * Stream entry'sini işle
     */
    private void processStreamEntry(String streamKey, String groupName, String consumerName, StreamEntry entry) {
        try {
            Map<String, String> fields = entry.getFields();

            String eventType = fields.get("event_type");
            String timestamp = fields.get("timestamp");

            logger.info("🔄 [{}:{}] Processing event: ID={}, Type={}, Time={}",
                    groupName, consumerName, entry.getID(), eventType, timestamp);

            // Simulate processing based on event type
            if ("user_login".equals(eventType)) {
                processUserLogin(fields);
            } else if ("order_created".equals(eventType)) {
                processOrderCreated(fields);
            } else if ("payment_processed".equals(eventType)) {
                processPaymentProcessed(fields);
            } else {
                processGenericEvent(fields);
            }

            // Simulate processing time
            Thread.sleep(100);

        } catch (Exception e) {
            logger.error("❌ Error processing stream entry", e);
        }
    }

    /**
     * User login event işleme
     */
    private void processUserLogin(Map<String, String> fields) {
        String userId = fields.get("user_id");
        String username = fields.get("username");

        logger.info("👤 User Login: {} (ID: {})", username, userId);

        // Business logic - update last login, session management, etc.
    }

    /**
     * Order created event işleme
     */
    private void processOrderCreated(Map<String, String> fields) {
        String orderId = fields.get("order_id");
        String userId = fields.get("user_id");
        String amount = fields.get("amount");

        logger.info("🛒 Order Created: {} (User: {}, Amount: {})", orderId, userId, amount);

        // Business logic - inventory update, payment processing, etc.
    }

    /**
     * Payment processed event işleme
     */
    private void processPaymentProcessed(Map<String, String> fields) {
        String paymentId = fields.get("payment_id");
        String orderId = fields.get("order_id");
        String status = fields.get("status");

        logger.info("💳 Payment Processed: {} (Order: {}, Status: {})", paymentId, orderId, status);

        // Business logic - order fulfillment, notification, etc.
    }

    /**
     * Generic event işleme
     */
    private void processGenericEvent(Map<String, String> fields) {
        logger.info("📋 Generic Event: {}", fields);
    }

    /**
     * Pending messages'ları al
     */
    public void handlePendingMessages(String streamKey, String groupName, String consumerName) {
        try (Jedis jedis = jedisPool.getResource()) {

            // Pending messages'ları al
            var pendingInfo = jedis.xpending(streamKey, groupName);

            if (pendingInfo.getTotal() > 0) {
                logger.info("⚠️ Found {} pending messages in group '{}'",
                        pendingInfo.getTotal(), groupName);

                // Pending messages'ları detaylı al
                var pendingMessages = jedis.xpending(streamKey, groupName,
                        StreamEntryID.MINIMUM, StreamEntryID.MAXIMUM,
                        10, consumerName);

                for (var pendingMessage : pendingMessages) {
                    StreamEntryID messageId = pendingMessage.getID();
                    long idleTime = pendingMessage.getIdleTime();

                    // 30 saniyeden fazla pending olan messages'ları yeniden işle
                    if (idleTime > 30000) {
                        logger.info("🔄 Reprocessing pending message: {} (idle: {} ms)",
                                messageId, idleTime);

                        // Message'ı claim et ve yeniden işle
                        var claimedMessages = jedis.xclaim(streamKey, groupName, consumerName,
                                30000, messageId);

                        for (StreamEntry claimedMessage : claimedMessages) {
                            processStreamEntry(streamKey, groupName, consumerName, claimedMessage);
                            acknowledgeMessage(streamKey, groupName, claimedMessage.getID());
                        }
                    }
                }
            }

        } catch (Exception e) {
            logger.error("❌ Error handling pending messages", e);
        }
    }

    /**
     * Stream trim - Eski event'leri temizle
     */
    public void trimStream(String streamKey, long maxLength) {
        try (Jedis jedis = jedisPool.getResource()) {

            Long removedCount = jedis.xtrim(streamKey, maxLength, true);

            logger.info("🗑️ Trimmed stream '{}': removed {} entries (max length: {})",
                    streamKey, removedCount, maxLength);

        } catch (Exception e) {
            logger.error("❌ Failed to trim stream", e);
        }
    }

    /**
     * Stream info
     */
    public void printStreamInfo(String streamKey) {
        try (Jedis jedis = jedisPool.getResource()) {

            var streamInfo = jedis.xinfoStream(streamKey);

            logger.info("📊 Stream '{}' Info:", streamKey);
            logger.info("  Length: {}", streamInfo.getLength());
            logger.info("  Groups: {}", streamInfo.getGroups());
            logger.info("  First Entry: {}", streamInfo.getFirstEntry());
            logger.info("  Last Entry: {}", streamInfo.getLastEntry());

        } catch (Exception e) {
            logger.error("❌ Failed to get stream info", e);
        }
    }

    /**
     * E-commerce event streaming demo
     */
    public void runEcommerceDemo() {
        logger.info("🚀 Starting E-commerce Event Streaming Demo...");

        try {
            isRunning.set(true);

            String streamKey = "ecommerce:events";
            String orderGroup = "order-processors";
            String analyticsGroup = "analytics-processors";
            String notificationGroup = "notification-processors";

            // Consumer groups oluştur
            createConsumerGroup(streamKey, orderGroup, "0");
            createConsumerGroup(streamKey, analyticsGroup, "0");
            createConsumerGroup(streamKey, notificationGroup, "0");

            // Consumer'ları başlat
            CompletableFuture<Void> orderProcessor = blockingReadFromConsumerGroup(
                    streamKey, orderGroup, "order-worker-1", 1000);

            CompletableFuture<Void> analyticsProcessor = blockingReadFromConsumerGroup(
                    streamKey, analyticsGroup, "analytics-worker-1", 1000);

            CompletableFuture<Void> notificationProcessor = blockingReadFromConsumerGroup(
                    streamKey, notificationGroup, "notification-worker-1", 1000);

            Thread.sleep(2000); // Wait for consumers to start

            // Simulate e-commerce events
            simulateEcommerceEvents(streamKey);

            Thread.sleep(5000); // Let consumers process events

            // Check pending messages
            handlePendingMessages(streamKey, orderGroup, "order-worker-1");
            handlePendingMessages(streamKey, analyticsGroup, "analytics-worker-1");
            handlePendingMessages(streamKey, notificationGroup, "notification-worker-1");

            // Print stream info
            printStreamInfo(streamKey);

            // Trim old events (keep last 1000)
            trimStream(streamKey, 1000);

        } catch (Exception e) {
            logger.error("❌ E-commerce demo error", e);
        } finally {
            isRunning.set(false);
        }
    }

    /**
     * E-commerce event'lerini simüle et
     */
    private void simulateEcommerceEvents(String streamKey) {
        logger.info("📝 Simulating e-commerce events...");

        // User login events
        for (int i = 1; i <= 5; i++) {
            Map<String, String> loginEvent = new HashMap<>();
            loginEvent.put("event_type", "user_login");
            loginEvent.put("user_id", "user" + i);
            loginEvent.put("username", "user" + i + "@example.com");
            loginEvent.put("ip_address", "192.168.1." + (100 + i));

            addEvent(streamKey, loginEvent);
        }

        // Order created events
        for (int i = 1; i <= 3; i++) {
            Map<String, String> orderEvent = new HashMap<>();
            orderEvent.put("event_type", "order_created");
            orderEvent.put("order_id", "order_" + (1000 + i));
            orderEvent.put("user_id", "user" + i);
            orderEvent.put("amount", String.valueOf(50.0 + (i * 25.0)));
            orderEvent.put("currency", "USD");
            orderEvent.put("items", String.valueOf(i + 1));

            addEvent(streamKey, orderEvent);
        }

        // Payment processed events
        for (int i = 1; i <= 3; i++) {
            Map<String, String> paymentEvent = new HashMap<>();
            paymentEvent.put("event_type", "payment_processed");
            paymentEvent.put("payment_id", "payment_" + (2000 + i));
            paymentEvent.put("order_id", "order_" + (1000 + i));
            paymentEvent.put("amount", String.valueOf(50.0 + (i * 25.0)));
            paymentEvent.put("status", i % 2 == 0 ? "SUCCESS" : "PENDING");
            paymentEvent.put("method", "credit_card");

            addEvent(streamKey, paymentEvent);
        }

        logger.info("✅ E-commerce events simulation completed");
    }

    /**
     * Performance test
     */
    public void runPerformanceTest() {
        logger.info("🏃 Starting Redis Streams Performance Test...");

        try {
            String streamKey = "performance:test";
            String groupName = "perf-group";

            createConsumerGroup(streamKey, groupName, "0");

            // Performance test - write throughput
            int eventCount = 1000;
            long startTime = System.currentTimeMillis();

            for (int i = 1; i <= eventCount; i++) {
                Map<String, String> event = new HashMap<>();
                event.put("event_type", "performance_test");
                event.put("sequence", String.valueOf(i));
                event.put("data", "test_data_" + i);

                addEvent(streamKey, event);

                if (i % 100 == 0) {
                    logger.info("📊 Progress: {}/{} events written", i, eventCount);
                }
            }

            long writeTime = System.currentTimeMillis() - startTime;
            double writeRate = (eventCount * 1000.0) / writeTime;

            logger.info("✅ Write Performance: {} events in {} ms ({:.2f} events/sec)",
                    eventCount, writeTime, writeRate);

            // Performance test - read throughput
            startTime = System.currentTimeMillis();
            int readCount = 0;

            while (true) {
                List<StreamEntry> entries = readFromConsumerGroup(streamKey, groupName, "perf-consumer", 100);
                if (entries.isEmpty()) {
                    break;
                }

                for (StreamEntry entry : entries) {
                    acknowledgeMessage(streamKey, groupName, entry.getID());
                }

                readCount += entries.size();
            }

            long readTime = System.currentTimeMillis() - startTime;
            double readRate = (readCount * 1000.0) / readTime;

            logger.info("✅ Read Performance: {} events in {} ms ({:.2f} events/sec)",
                    readCount, readTime, readRate);

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
     * Main method
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java StreamsExample <mode>");
            System.out.println("Modes:");
            System.out.println("  ecommerce   - E-commerce event streaming demo");
            System.out.println("  performance - Performance test");
            System.out.println("  basic       - Basic streams demo");
            return;
        }

        String mode = args[0].toLowerCase();
        StreamsExample streamsExample = new StreamsExample();
        streamsExample.setupShutdownHook();

        try {
            switch (mode) {
                case "ecommerce":
                    streamsExample.runEcommerceDemo();
                    break;

                case "performance":
                    streamsExample.runPerformanceTest();
                    break;

                case "basic":
                    streamsExample.runBasicDemo();
                    break;

                default:
                    logger.error("❌ Unknown mode: {}", mode);
                    return;
            }

            // Keep application running for some time
            Thread.sleep(10000);

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            logger.info("⚠️ Application interrupted");
        } catch (Exception e) {
            logger.error("❌ Application error", e);
        } finally {
            streamsExample.close();
        }
    }

    /**
     * Basic streams demo
     */
    private void runBasicDemo() {
        logger.info("🚀 Starting Basic Streams Demo...");

        try {
            String streamKey = "basic:events";
            String groupName = "basic-group";

            createConsumerGroup(streamKey, groupName, "0");

            // Add some events
            Map<String, String> event1 = new HashMap<>();
            event1.put("event_type", "test");
            event1.put("message", "Hello Redis Streams!");
            addEvent(streamKey, event1);

            Map<String, String> event2 = new HashMap<>();
            event2.put("event_type", "info");
            event2.put("message", "This is a basic demo");
            addEvent(streamKey, event2);

            // Read events
            List<StreamEntry> entries = readFromConsumerGroup(streamKey, groupName, "basic-consumer", 10);

            for (StreamEntry entry : entries) {
                logger.info("📖 Read event: ID={}, Fields={}", entry.getID(), entry.getFields());
                acknowledgeMessage(streamKey, groupName, entry.getID());
            }

            printStreamInfo(streamKey);

        } catch (Exception e) {
            logger.error("❌ Basic demo error", e);
        }
    }
}