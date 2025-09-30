package com.example.rabbitmq;

import com.rabbitmq.client.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeoutException;

/**
 * RabbitMQ Exchange Patterns - Farklı exchange türleri ve kullanımları
 * 
 * Bu sınıf RabbitMQ'nun farklı exchange pattern'lerini gösterir:
 * - Direct Exchange - Exact routing key matching
 * - Topic Exchange - Pattern-based routing
 * - Fanout Exchange - Broadcast messaging
 * - Headers Exchange - Header-based routing
 * - Dead Letter Exchange (DLX) - Error handling
 */
public class ExchangePatterns {

    private static final Logger logger = LoggerFactory.getLogger(ExchangePatterns.class);

    // RabbitMQ connection parameters
    private static final String HOST = "localhost";
    private static final int PORT = 5672;
    private static final String USERNAME = "admin";
    private static final String PASSWORD = "admin123";

    // Exchange names
    private static final String DIRECT_EXCHANGE = "order_processing";
    private static final String TOPIC_EXCHANGE = "log_routing";
    private static final String FANOUT_EXCHANGE = "notifications";
    private static final String HEADERS_EXCHANGE = "task_routing";
    private static final String DLX_EXCHANGE = "dead_letter_exchange";

    private Connection connection;
    private Channel channel;
    private ObjectMapper objectMapper;

    public ExchangePatterns() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
    }

    /**
     * RabbitMQ bağlantısı oluştur
     */
    public void connect() throws IOException, TimeoutException {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost(HOST);
        factory.setPort(PORT);
        factory.setUsername(USERNAME);
        factory.setPassword(PASSWORD);

        factory.setAutomaticRecoveryEnabled(true);
        factory.setNetworkRecoveryInterval(10000);

        try {
            connection = factory.newConnection();
            channel = connection.createChannel();

            logger.info("✅ RabbitMQ Exchange Patterns connection established");
        } catch (IOException | TimeoutException e) {
            logger.error("❌ RabbitMQ connection failed", e);
            throw e;
        }
    }

    /**
     * Exchange'leri ve queue'ları setup et
     */
    public void setupExchangesAndQueues() throws IOException {
        // 1. Direct Exchange Setup
        setupDirectExchange();

        // 2. Topic Exchange Setup
        setupTopicExchange();

        // 3. Fanout Exchange Setup
        setupFanoutExchange();

        // 4. Headers Exchange Setup
        setupHeadersExchange();

        // 5. Dead Letter Exchange Setup
        setupDeadLetterExchange();

        logger.info("🏗️ All exchanges and queues setup completed");
    }

    /**
     * Direct Exchange - Exact routing key matching
     * 
     * Use case: Order processing system
     * - Different queues for different order types
     * - Exact matching between routing key and queue binding
     */
    private void setupDirectExchange() throws IOException {
        // Direct exchange declare
        channel.exchangeDeclare(DIRECT_EXCHANGE, BuiltinExchangeType.DIRECT, true);

        // Order processing queues
        channel.queueDeclare("orders.new", true, false, false, null);
        channel.queueDeclare("orders.payment", true, false, false, null);
        channel.queueDeclare("orders.shipping", true, false, false, null);
        channel.queueDeclare("orders.completed", true, false, false, null);

        // Bind queues to exchange with specific routing keys
        channel.queueBind("orders.new", DIRECT_EXCHANGE, "order.new");
        channel.queueBind("orders.payment", DIRECT_EXCHANGE, "order.payment");
        channel.queueBind("orders.shipping", DIRECT_EXCHANGE, "order.shipping");
        channel.queueBind("orders.completed", DIRECT_EXCHANGE, "order.completed");

        logger.info("🎯 Direct Exchange '{}' setup completed", DIRECT_EXCHANGE);
    }

    /**
     * Topic Exchange - Pattern-based routing
     * 
     * Use case: Logging system
     * - Different log levels and services
     * - Pattern matching with wildcards (* and #)
     */
    private void setupTopicExchange() throws IOException {
        // Topic exchange declare
        channel.exchangeDeclare(TOPIC_EXCHANGE, BuiltinExchangeType.TOPIC, true);

        // Log processing queues
        channel.queueDeclare("logs.all", true, false, false, null);
        channel.queueDeclare("logs.errors", true, false, false, null);
        channel.queueDeclare("logs.auth_service", true, false, false, null);
        channel.queueDeclare("logs.payment_service", true, false, false, null);

        // Topic bindings with patterns
        channel.queueBind("logs.all", TOPIC_EXCHANGE, "logs.*.*"); // All logs
        channel.queueBind("logs.errors", TOPIC_EXCHANGE, "logs.*.error"); // All error logs
        channel.queueBind("logs.auth_service", TOPIC_EXCHANGE, "logs.auth.*"); // All auth service logs
        channel.queueBind("logs.payment_service", TOPIC_EXCHANGE, "logs.payment.*"); // All payment service logs

        logger.info("🔀 Topic Exchange '{}' setup completed", TOPIC_EXCHANGE);
    }

    /**
     * Fanout Exchange - Broadcast messaging
     * 
     * Use case: Notification system
     * - Broadcast messages to all subscribers
     * - No routing key consideration
     */
    private void setupFanoutExchange() throws IOException {
        // Fanout exchange declare
        channel.exchangeDeclare(FANOUT_EXCHANGE, BuiltinExchangeType.FANOUT, true);

        // Notification queues (different channels)
        channel.queueDeclare("notifications.email", true, false, false, null);
        channel.queueDeclare("notifications.sms", true, false, false, null);
        channel.queueDeclare("notifications.push", true, false, false, null);
        channel.queueDeclare("notifications.slack", true, false, false, null);

        // Bind all queues to fanout exchange (routing key ignored)
        channel.queueBind("notifications.email", FANOUT_EXCHANGE, "");
        channel.queueBind("notifications.sms", FANOUT_EXCHANGE, "");
        channel.queueBind("notifications.push", FANOUT_EXCHANGE, "");
        channel.queueBind("notifications.slack", FANOUT_EXCHANGE, "");

        logger.info("📢 Fanout Exchange '{}' setup completed", FANOUT_EXCHANGE);
    }

    /**
     * Headers Exchange - Header-based routing
     * 
     * Use case: Task routing system
     * - Route based on message headers
     * - Complex routing logic
     */
    private void setupHeadersExchange() throws IOException {
        // Headers exchange declare
        channel.exchangeDeclare(HEADERS_EXCHANGE, BuiltinExchangeType.HEADERS, true);

        // Task processing queues
        channel.queueDeclare("tasks.high_priority", true, false, false, null);
        channel.queueDeclare("tasks.cpu_intensive", true, false, false, null);
        channel.queueDeclare("tasks.io_intensive", true, false, false, null);
        channel.queueDeclare("tasks.background", true, false, false, null);

        // Headers-based bindings
        Map<String, Object> highPriorityHeaders = new HashMap<>();
        highPriorityHeaders.put("x-match", "any");
        highPriorityHeaders.put("priority", "high");
        highPriorityHeaders.put("urgent", "true");
        channel.queueBind("tasks.high_priority", HEADERS_EXCHANGE, "", highPriorityHeaders);

        Map<String, Object> cpuIntensiveHeaders = new HashMap<>();
        cpuIntensiveHeaders.put("x-match", "all");
        cpuIntensiveHeaders.put("task_type", "cpu");
        cpuIntensiveHeaders.put("resource_intensive", "true");
        channel.queueBind("tasks.cpu_intensive", HEADERS_EXCHANGE, "", cpuIntensiveHeaders);

        Map<String, Object> ioIntensiveHeaders = new HashMap<>();
        ioIntensiveHeaders.put("x-match", "all");
        ioIntensiveHeaders.put("task_type", "io");
        ioIntensiveHeaders.put("resource_intensive", "true");
        channel.queueBind("tasks.io_intensive", HEADERS_EXCHANGE, "", ioIntensiveHeaders);

        Map<String, Object> backgroundHeaders = new HashMap<>();
        backgroundHeaders.put("x-match", "any");
        backgroundHeaders.put("priority", "low");
        backgroundHeaders.put("background", "true");
        channel.queueBind("tasks.background", HEADERS_EXCHANGE, "", backgroundHeaders);

        logger.info("🏷️ Headers Exchange '{}' setup completed", HEADERS_EXCHANGE);
    }

    /**
     * Dead Letter Exchange - Error handling
     * 
     * Use case: Failed message handling
     * - Messages that fail processing
     * - TTL expired messages
     * - Queue length exceeded messages
     */
    private void setupDeadLetterExchange() throws IOException {
        // Dead letter exchange declare
        channel.exchangeDeclare(DLX_EXCHANGE, BuiltinExchangeType.DIRECT, true);

        // Dead letter queue
        channel.queueDeclare("dead_letters", true, false, false, null);
        channel.queueBind("dead_letters", DLX_EXCHANGE, "failed");

        // Main processing queue with DLX configuration
        Map<String, Object> queueArgs = new HashMap<>();
        queueArgs.put("x-dead-letter-exchange", DLX_EXCHANGE);
        queueArgs.put("x-dead-letter-routing-key", "failed");
        queueArgs.put("x-message-ttl", 60000); // 60 seconds TTL
        queueArgs.put("x-max-length", 1000); // Max 1000 messages

        channel.queueDeclare("processing_queue", true, false, false, queueArgs);

        logger.info("💀 Dead Letter Exchange '{}' setup completed", DLX_EXCHANGE);
    }

    /**
     * Direct Exchange Demo - Order processing
     */
    public void demonstrateDirectExchange() throws IOException {
        logger.info("🎯 Direct Exchange Demo - Order Processing");

        // Order lifecycle messages
        publishDirectMessage("order.new", createOrderMessage("new", "ORD001", "user123", 99.99));
        publishDirectMessage("order.payment", createOrderMessage("payment_received", "ORD001", "user123", 99.99));
        publishDirectMessage("order.shipping", createOrderMessage("shipped", "ORD001", "user123", 99.99));
        publishDirectMessage("order.completed", createOrderMessage("completed", "ORD001", "user123", 99.99));

        // Different order
        publishDirectMessage("order.new", createOrderMessage("new", "ORD002", "user456", 149.99));
        publishDirectMessage("order.payment", createOrderMessage("payment_failed", "ORD002", "user456", 149.99));
    }

    /**
     * Topic Exchange Demo - Logging system
     */
    public void demonstrateTopicExchange() throws IOException {
        logger.info("🔀 Topic Exchange Demo - Logging System");

        // Different service logs
        publishTopicMessage("logs.auth.info", createLogMessage("info", "auth", "User login successful"));
        publishTopicMessage("logs.auth.error", createLogMessage("error", "auth", "Invalid credentials"));
        publishTopicMessage("logs.payment.info", createLogMessage("info", "payment", "Payment processed"));
        publishTopicMessage("logs.payment.error", createLogMessage("error", "payment", "Payment gateway timeout"));
        publishTopicMessage("logs.order.info", createLogMessage("info", "order", "Order created"));
        publishTopicMessage("logs.order.warning", createLogMessage("warning", "order", "Low inventory"));
    }

    /**
     * Fanout Exchange Demo - Notification broadcast
     */
    public void demonstrateFanoutExchange() throws IOException {
        logger.info("📢 Fanout Exchange Demo - Notification Broadcast");

        // Broadcast notifications (all channels will receive these)
        publishFanoutMessage(createNotificationMessage("system_maintenance",
                "System maintenance scheduled for tonight at 2 AM"));
        publishFanoutMessage(createNotificationMessage("new_feature",
                "New feature released: Advanced analytics dashboard"));
        publishFanoutMessage(createNotificationMessage("security_alert",
                "Suspicious login activity detected"));
    }

    /**
     * Headers Exchange Demo - Task routing
     */
    public void demonstrateHeadersExchange() throws IOException {
        logger.info("🏷️ Headers Exchange Demo - Task Routing");

        // High priority task
        Map<String, Object> highPriorityHeaders = new HashMap<>();
        highPriorityHeaders.put("priority", "high");
        highPriorityHeaders.put("urgent", "true");
        publishHeadersMessage(highPriorityHeaders,
                createTaskMessage("urgent_report", "Generate urgent financial report"));

        // CPU intensive task
        Map<String, Object> cpuHeaders = new HashMap<>();
        cpuHeaders.put("task_type", "cpu");
        cpuHeaders.put("resource_intensive", "true");
        cpuHeaders.put("estimated_duration", "300");
        publishHeadersMessage(cpuHeaders, createTaskMessage("data_analysis", "Process large dataset"));

        // IO intensive task
        Map<String, Object> ioHeaders = new HashMap<>();
        ioHeaders.put("task_type", "io");
        ioHeaders.put("resource_intensive", "true");
        ioHeaders.put("file_size", "large");
        publishHeadersMessage(ioHeaders, createTaskMessage("file_backup", "Backup user files"));

        // Background task
        Map<String, Object> backgroundHeaders = new HashMap<>();
        backgroundHeaders.put("priority", "low");
        backgroundHeaders.put("background", "true");
        publishHeadersMessage(backgroundHeaders, createTaskMessage("cleanup", "Clean temporary files"));
    }

    /**
     * Dead Letter Exchange Demo
     */
    public void demonstrateDeadLetterExchange() throws IOException {
        logger.info("💀 Dead Letter Exchange Demo - Error Handling");

        // Send messages to processing queue (some will fail/expire)
        for (int i = 1; i <= 5; i++) {
            Map<String, Object> message = createProcessingMessage("task_" + i, "Process item " + i);

            // Simulate different scenarios
            if (i == 3) {
                message.put("will_fail", true); // This will cause processing failure
            }

            publishToProcessingQueue(message);
        }
    }

    /**
     * Direct exchange message publish
     */
    private void publishDirectMessage(String routingKey, Map<String, Object> message) throws IOException {
        String jsonMessage = objectMapper.writeValueAsString(message);

        AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                .deliveryMode(2) // Persistent
                .contentType("application/json")
                .timestamp(new java.util.Date())
                .build();

        channel.basicPublish(DIRECT_EXCHANGE, routingKey, properties, jsonMessage.getBytes("UTF-8"));
        logger.info("📤 Direct: {} -> {}", routingKey, message.get("order_id"));
    }

    /**
     * Topic exchange message publish
     */
    private void publishTopicMessage(String routingKey, Map<String, Object> message) throws IOException {
        String jsonMessage = objectMapper.writeValueAsString(message);

        AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                .deliveryMode(1) // Non-persistent for logs
                .contentType("application/json")
                .timestamp(new java.util.Date())
                .build();

        channel.basicPublish(TOPIC_EXCHANGE, routingKey, properties, jsonMessage.getBytes("UTF-8"));
        logger.info("📤 Topic: {} -> {}.{}", routingKey, message.get("service"), message.get("level"));
    }

    /**
     * Fanout exchange message publish
     */
    private void publishFanoutMessage(Map<String, Object> message) throws IOException {
        String jsonMessage = objectMapper.writeValueAsString(message);

        AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                .deliveryMode(1) // Non-persistent for notifications
                .contentType("application/json")
                .timestamp(new java.util.Date())
                .build();

        channel.basicPublish(FANOUT_EXCHANGE, "", properties, jsonMessage.getBytes("UTF-8"));
        logger.info("📤 Fanout: {} (broadcast)", message.get("type"));
    }

    /**
     * Headers exchange message publish
     */
    private void publishHeadersMessage(Map<String, Object> headers, Map<String, Object> message) throws IOException {
        String jsonMessage = objectMapper.writeValueAsString(message);

        AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                .deliveryMode(2) // Persistent for tasks
                .contentType("application/json")
                .timestamp(new java.util.Date())
                .headers(headers)
                .build();

        channel.basicPublish(HEADERS_EXCHANGE, "", properties, jsonMessage.getBytes("UTF-8"));
        logger.info("📤 Headers: {} -> {} (headers: {})", message.get("task_type"), message.get("task_id"), headers);
    }

    /**
     * Processing queue message publish
     */
    private void publishToProcessingQueue(Map<String, Object> message) throws IOException {
        String jsonMessage = objectMapper.writeValueAsString(message);

        AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                .deliveryMode(2) // Persistent
                .contentType("application/json")
                .timestamp(new java.util.Date())
                .build();

        channel.basicPublish("", "processing_queue", properties, jsonMessage.getBytes("UTF-8"));
        logger.info("📤 Processing: {}", message.get("task_id"));
    }

    /**
     * Helper methods for creating different message types
     */
    private Map<String, Object> createOrderMessage(String status, String orderId, String userId, double amount) {
        Map<String, Object> message = new HashMap<>();
        message.put("order_id", orderId);
        message.put("user_id", userId);
        message.put("status", status);
        message.put("amount", amount);
        message.put("timestamp", LocalDateTime.now().toString());
        message.put("processing_time", System.currentTimeMillis());
        return message;
    }

    private Map<String, Object> createLogMessage(String level, String service, String message) {
        Map<String, Object> logMessage = new HashMap<>();
        logMessage.put("level", level.toUpperCase());
        logMessage.put("service", service);
        logMessage.put("message", message);
        logMessage.put("timestamp", LocalDateTime.now().toString());
        logMessage.put("thread", Thread.currentThread().getName());
        return logMessage;
    }

    private Map<String, Object> createNotificationMessage(String type, String content) {
        Map<String, Object> notification = new HashMap<>();
        notification.put("type", type);
        notification.put("content", content);
        notification.put("timestamp", LocalDateTime.now().toString());
        notification.put("notification_id", UUID.randomUUID().toString());
        notification.put("priority", "normal");
        return notification;
    }

    private Map<String, Object> createTaskMessage(String taskType, String description) {
        Map<String, Object> task = new HashMap<>();
        task.put("task_id", "task_" + System.currentTimeMillis());
        task.put("task_type", taskType);
        task.put("description", description);
        task.put("created_at", LocalDateTime.now().toString());
        task.put("status", "pending");
        return task;
    }

    private Map<String, Object> createProcessingMessage(String taskId, String description) {
        Map<String, Object> message = new HashMap<>();
        message.put("task_id", taskId);
        message.put("description", description);
        message.put("created_at", LocalDateTime.now().toString());
        message.put("attempts", 0);
        return message;
    }

    /**
     * Complete exchange patterns demo
     */
    public void runCompleteDemo() throws IOException, InterruptedException {
        logger.info("🚀 Starting Complete Exchange Patterns Demo...");

        // Setup all exchanges and queues
        setupExchangesAndQueues();

        Thread.sleep(1000); // Wait for setup

        // Demonstrate each exchange type
        demonstrateDirectExchange();
        Thread.sleep(500);

        demonstrateTopicExchange();
        Thread.sleep(500);

        demonstrateFanoutExchange();
        Thread.sleep(500);

        demonstrateHeadersExchange();
        Thread.sleep(500);

        demonstrateDeadLetterExchange();

        logger.info("✅ Complete Exchange Patterns Demo finished!");
    }

    /**
     * Resource cleanup
     */
    public void close() throws IOException, TimeoutException {
        if (channel != null && channel.isOpen()) {
            channel.close();
        }
        if (connection != null && connection.isOpen()) {
            connection.close();
        }
        logger.info("🔒 RabbitMQ Exchange Patterns connection closed");
    }

    /**
     * Main method
     */
    public static void main(String[] args) {
        ExchangePatterns exchangePatterns = new ExchangePatterns();

        try {
            // Connect
            exchangePatterns.connect();

            // Run demo based on argument
            if (args.length > 0) {
                String mode = args[0].toLowerCase();
                switch (mode) {
                    case "direct":
                        exchangePatterns.setupExchangesAndQueues();
                        exchangePatterns.demonstrateDirectExchange();
                        break;
                    case "topic":
                        exchangePatterns.setupExchangesAndQueues();
                        exchangePatterns.demonstrateTopicExchange();
                        break;
                    case "fanout":
                        exchangePatterns.setupExchangesAndQueues();
                        exchangePatterns.demonstrateFanoutExchange();
                        break;
                    case "headers":
                        exchangePatterns.setupExchangesAndQueues();
                        exchangePatterns.demonstrateHeadersExchange();
                        break;
                    case "dlx":
                        exchangePatterns.setupExchangesAndQueues();
                        exchangePatterns.demonstrateDeadLetterExchange();
                        break;
                    default:
                        exchangePatterns.runCompleteDemo();
                }
            } else {
                // Run complete demo
                exchangePatterns.runCompleteDemo();
            }

        } catch (Exception e) {
            logger.error("❌ Exchange patterns demo error", e);
        } finally {
            try {
                exchangePatterns.close();
            } catch (Exception e) {
                logger.error("❌ Error closing connection", e);
            }
        }
    }
}