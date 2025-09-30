import com.rabbitmq.client.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;
import java.util.concurrent.TimeoutException;
import java.io.IOException;

/**
 * RabbitMQ Simple Producer
 * 
 * Bu sınıf basit mesaj gönderme işlemlerini gösterir.
 * Hem basit queue hem de exchange'li mesajlaşma örnekleri içerir.
 */
public class SimpleProducer {

    private static final Logger logger = LoggerFactory.getLogger(SimpleProducer.class);

    // RabbitMQ connection parameters
    private static final String HOST = "localhost";
    private static final int PORT = 5672;
    private static final String USERNAME = "admin";
    private static final String PASSWORD = "admin123";

    // Queue and Exchange names
    private static final String SIMPLE_QUEUE = "hello";
    private static final String TASK_QUEUE = "task_queue";
    private static final String LOGS_EXCHANGE = "logs";

    private Connection connection;
    private Channel channel;
    private ObjectMapper objectMapper;

    public SimpleProducer() {
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

        // Connection recovery ayarları
        factory.setAutomaticRecoveryEnabled(true);
        factory.setNetworkRecoveryInterval(10000);

        try {
            connection = factory.newConnection();
            channel = connection.createChannel();
            logger.info("✅ RabbitMQ'ya bağlandı");
        } catch (IOException | TimeoutException e) {
            logger.error("❌ RabbitMQ bağlantı hatası", e);
            throw e;
        }
    }

    /**
     * Basit mesaj gönderme
     */
    public void sendSimpleMessage(String message) throws IOException {
        // Queue declare et (idempotent)
        channel.queueDeclare(SIMPLE_QUEUE, true, false, false, null);

        // Mesaj verilerini hazırla
        Map<String, Object> messageData = new HashMap<>();
        messageData.put("message", message);
        messageData.put("timestamp", LocalDateTime.now().toString());
        messageData.put("sender", "SimpleProducer");
        messageData.put("type", "simple_message");

        try {
            String jsonMessage = objectMapper.writeValueAsString(messageData);

            // Mesaj properties
            AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                    .deliveryMode(2) // Persistent message
                    .contentType("application/json")
                    .timestamp(new java.util.Date())
                    .build();

            // Mesaj gönder
            channel.basicPublish("", SIMPLE_QUEUE, properties, jsonMessage.getBytes("UTF-8"));

            logger.info("📤 Basit mesaj gönderildi: {}", message);

        } catch (Exception e) {
            logger.error("❌ Mesaj gönderme hatası", e);
            throw new IOException("Message sending failed", e);
        }
    }

    /**
     * Work queue'ya task gönderme
     */
    public void sendTask(String task, int priority) throws IOException {
        // Durable queue declare et
        Map<String, Object> args = new HashMap<>();
        args.put("x-max-priority", 10); // Priority queue

        channel.queueDeclare(TASK_QUEUE, true, false, false, args);

        // Task verilerini hazırla
        Map<String, Object> taskData = new HashMap<>();
        taskData.put("task", task);
        taskData.put("priority", priority);
        taskData.put("timestamp", LocalDateTime.now().toString());
        taskData.put("sender", "SimpleProducer");
        taskData.put("estimated_duration", calculateEstimatedDuration(task));

        try {
            String jsonTask = objectMapper.writeValueAsString(taskData);

            // Task properties with priority
            AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                    .deliveryMode(2) // Persistent
                    .priority(priority)
                    .contentType("application/json")
                    .headers(createTaskHeaders(task, priority))
                    .build();

            // Task gönder
            channel.basicPublish("", TASK_QUEUE, properties, jsonTask.getBytes("UTF-8"));

            logger.info("🔧 Task gönderildi: {} (Priority: {})", task, priority);

        } catch (Exception e) {
            logger.error("❌ Task gönderme hatası", e);
            throw new IOException("Task sending failed", e);
        }
    }

    /**
     * Fanout exchange'e log mesajı gönderme
     */
    public void sendLogMessage(String level, String message) throws IOException {
        // Fanout exchange declare et
        channel.exchangeDeclare(LOGS_EXCHANGE, BuiltinExchangeType.FANOUT, true);

        // Log verilerini hazırla
        Map<String, Object> logData = new HashMap<>();
        logData.put("level", level.toUpperCase());
        logData.put("message", message);
        logData.put("timestamp", LocalDateTime.now().toString());
        logData.put("source", "SimpleProducer");
        logData.put("thread", Thread.currentThread().getName());

        try {
            String jsonLog = objectMapper.writeValueAsString(logData);

            // Log properties
            AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                    .deliveryMode(1) // Non-persistent for logs
                    .contentType("application/json")
                    .headers(createLogHeaders(level))
                    .build();

            // Log mesajını fanout exchange'e gönder
            channel.basicPublish(LOGS_EXCHANGE, "", properties, jsonLog.getBytes("UTF-8"));

            logger.info("📝 Log gönderildi: [{}] {}", level.toUpperCase(), message);

        } catch (Exception e) {
            logger.error("❌ Log gönderme hatası", e);
            throw new IOException("Log sending failed", e);
        }
    }

    /**
     * Batch mesaj gönderme
     */
    public void sendBatchMessages(String prefix, int count) throws IOException {
        logger.info("📦 Batch mesaj gönderiliyor: {} adet", count);

        long startTime = System.currentTimeMillis();

        for (int i = 1; i <= count; i++) {
            String message = String.format("%s - Mesaj #%d", prefix, i);
            sendSimpleMessage(message);

            // Her 100 mesajda bir progress göster
            if (i % 100 == 0) {
                logger.info("📊 Progress: {}/{} mesaj gönderildi", i, count);
            }
        }

        long duration = System.currentTimeMillis() - startTime;
        double messagesPerSecond = (count * 1000.0) / duration;

        logger.info("✅ Batch tamamlandı: {} mesaj, {} ms, {:.2f} msg/sec",
                count, duration, messagesPerSecond);
    }

    /**
     * Task için tahmini süre hesapla
     */
    private int calculateEstimatedDuration(String task) {
        // Basit hesaplama: kelime sayısına göre
        String[] words = task.split("\\s+");
        return Math.max(1, words.length * 2); // Kelime başına 2 saniye
    }

    /**
     * Task için header'lar oluştur
     */
    private Map<String, Object> createTaskHeaders(String task, int priority) {
        Map<String, Object> headers = new HashMap<>();
        headers.put("task-type", determineTaskType(task));
        headers.put("priority-level", getPriorityLevel(priority));
        headers.put("estimated-duration", calculateEstimatedDuration(task));
        return headers;
    }

    /**
     * Log için header'lar oluştur
     */
    private Map<String, Object> createLogHeaders(String level) {
        Map<String, Object> headers = new HashMap<>();
        headers.put("log-level", level.toUpperCase());
        headers.put("severity", getLogSeverity(level));
        headers.put("application", "rabbitmq-examples");
        return headers;
    }

    /**
     * Task tipini belirle
     */
    private String determineTaskType(String task) {
        String lowerTask = task.toLowerCase();
        if (lowerTask.contains("process") || lowerTask.contains("calculate")) {
            return "COMPUTE";
        } else if (lowerTask.contains("send") || lowerTask.contains("email")) {
            return "COMMUNICATION";
        } else if (lowerTask.contains("backup") || lowerTask.contains("save")) {
            return "STORAGE";
        } else {
            return "GENERAL";
        }
    }

    /**
     * Priority level string'i
     */
    private String getPriorityLevel(int priority) {
        if (priority >= 8)
            return "CRITICAL";
        if (priority >= 6)
            return "HIGH";
        if (priority >= 4)
            return "MEDIUM";
        if (priority >= 2)
            return "LOW";
        return "MINIMAL";
    }

    /**
     * Log severity değeri
     */
    private int getLogSeverity(String level) {
        switch (level.toUpperCase()) {
            case "ERROR":
                return 1;
            case "WARN":
                return 2;
            case "INFO":
                return 3;
            case "DEBUG":
                return 4;
            default:
                return 5;
        }
    }

    /**
     * Bağlantıyı kapat
     */
    public void close() throws IOException, TimeoutException {
        if (channel != null && channel.isOpen()) {
            channel.close();
        }
        if (connection != null && connection.isOpen()) {
            connection.close();
        }
        logger.info("🔒 RabbitMQ bağlantısı kapatıldı");
    }

    /**
     * Interactive CLI
     */
    public void runInteractive() {
        Scanner scanner = new Scanner(System.in);

        System.out.println("\n🐰 RabbitMQ Producer - Interactive Mode");
        System.out.println("=====================================");
        System.out.println("Komutlar:");
        System.out.println("  1 <mesaj>           - Basit mesaj gönder");
        System.out.println("  2 <task> <priority> - Task gönder (priority: 1-10)");
        System.out.println("  3 <level> <mesaj>   - Log gönder (level: info,warn,error)");
        System.out.println("  4 <prefix> <count>  - Batch mesaj gönder");
        System.out.println("  quit                - Çıkış");
        System.out.println();

        while (true) {
            System.out.print("Producer> ");
            String input = scanner.nextLine().trim();

            if (input.equalsIgnoreCase("quit") || input.equalsIgnoreCase("exit")) {
                break;
            }

            try {
                processCommand(input);
            } catch (Exception e) {
                logger.error("❌ Komut işleme hatası: {}", e.getMessage());
            }
        }

        scanner.close();
    }

    /**
     * Komut işleme
     */
    private void processCommand(String input) throws IOException {
        String[] parts = input.split("\\s+", 3);

        if (parts.length == 0) {
            return;
        }

        String command = parts[0];

        switch (command) {
            case "1":
                if (parts.length >= 2) {
                    String message = String.join(" ", java.util.Arrays.copyOfRange(parts, 1, parts.length));
                    sendSimpleMessage(message);
                } else {
                    System.out.println("❌ Format: 1 <mesaj>");
                }
                break;

            case "2":
                if (parts.length >= 3) {
                    try {
                        String task = parts[1];
                        int priority = Integer.parseInt(parts[2]);
                        if (priority < 1 || priority > 10) {
                            System.out.println("❌ Priority 1-10 arasında olmalı");
                        } else {
                            sendTask(task, priority);
                        }
                    } catch (NumberFormatException e) {
                        System.out.println("❌ Priority sayı olmalı");
                    }
                } else {
                    System.out.println("❌ Format: 2 <task> <priority>");
                }
                break;

            case "3":
                if (parts.length >= 3) {
                    String level = parts[1];
                    String message = String.join(" ", java.util.Arrays.copyOfRange(parts, 2, parts.length));
                    sendLogMessage(level, message);
                } else {
                    System.out.println("❌ Format: 3 <level> <mesaj>");
                }
                break;

            case "4":
                if (parts.length >= 3) {
                    try {
                        String prefix = parts[1];
                        int count = Integer.parseInt(parts[2]);
                        if (count > 0 && count <= 10000) {
                            sendBatchMessages(prefix, count);
                        } else {
                            System.out.println("❌ Count 1-10000 arasında olmalı");
                        }
                    } catch (NumberFormatException e) {
                        System.out.println("❌ Count sayı olmalı");
                    }
                } else {
                    System.out.println("❌ Format: 4 <prefix> <count>");
                }
                break;

            default:
                System.out.println("❌ Bilinmeyen komut: " + command);
        }
    }

    /**
     * Main method
     */
    public static void main(String[] args) {
        SimpleProducer producer = new SimpleProducer();

        try {
            // Bağlan
            producer.connect();

            if (args.length > 0) {
                // Komut satırı argumentları ile çalıştır
                String message = String.join(" ", args);
                producer.sendSimpleMessage(message);

                // Örnek gösterimler
                producer.sendTask("Process customer orders", 8);
                producer.sendTask("Backup database", 3);
                producer.sendLogMessage("info", "Application started successfully");
                producer.sendLogMessage("warn", "High memory usage detected");

            } else {
                // Interactive mode
                producer.runInteractive();
            }

        } catch (Exception e) {
            logger.error("❌ Producer hatası", e);
        } finally {
            try {
                producer.close();
            } catch (Exception e) {
                logger.error("❌ Bağlantı kapatma hatası", e);
            }
        }
    }
}