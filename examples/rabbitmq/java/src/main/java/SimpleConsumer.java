package com.example.rabbitmq;

import com.rabbitmq.client.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeoutException;

/**
 * RabbitMQ Simple Consumer
 * 
 * Bu sınıf farklı consumer pattern'lerini gösterir:
 * - Basit queue consumer
 * - Work queue consumer (ack/nack handling)
 * - Fanout exchange consumer
 * - Priority queue consumer
 * - Manual acknowledgment handling
 */
public class SimpleConsumer {

    private static final Logger logger = LoggerFactory.getLogger(SimpleConsumer.class);

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
    private String consumerTag;

    public SimpleConsumer() {
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

        // Consumer için prefetch ayarı
        try {
            connection = factory.newConnection();
            channel = connection.createChannel();

            // Fair dispatch - worker'lar arası load balancing için
            channel.basicQos(1);

            logger.info("✅ RabbitMQ'ya bağlandı");
        } catch (IOException | TimeoutException e) {
            logger.error("❌ RabbitMQ bağlantı hatası", e);
            throw e;
        }
    }

    /**
     * Basit mesaj tüketme - Auto acknowledgment
     * 
     * Avantajları:
     * - Simple implementation
     * - Automatic message acknowledgment
     * 
     * Dezavantajları:
     * - Risk of message loss on failure
     * - No control over acknowledgment timing
     */
    public void consumeSimpleMessages() throws IOException {
        // Queue declare et
        channel.queueDeclare(SIMPLE_QUEUE, true, false, false, null);

        logger.info("🔄 Basit mesajlar dinleniyor... Çıkmak için CTRL+C");

        // Auto-ack consumer
        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            try {
                String message = new String(delivery.getBody(), "UTF-8");

                // JSON parse et
                @SuppressWarnings("unchecked")
                Map<String, Object> messageData = objectMapper.readValue(message, Map.class);

                // Mesajı işle
                processSimpleMessage(messageData, delivery.getProperties());

                logger.info("✅ Basit mesaj işlendi: {}", messageData.get("message"));

            } catch (Exception e) {
                logger.error("❌ Mesaj işleme hatası", e);
            }
        };

        CancelCallback cancelCallback = consumerTag -> {
            logger.info("⚠️ Consumer iptal edildi: {}", consumerTag);
        };

        // Consumer'ı başlat (auto-ack enabled)
        this.consumerTag = channel.basicConsume(SIMPLE_QUEUE, true, deliverCallback, cancelCallback);
    }

    /**
     * Work queue consumer - Manual acknowledgment
     * 
     * Avantajları:
     * - Full control over message acknowledgment
     * - No message loss on processing failure
     * - Retry mechanism support
     * 
     * Dezavantajları:
     * - More complex implementation
     * - Manual error handling required
     */
    public void consumeWorkQueue() throws IOException {
        // Durable queue declare et
        Map<String, Object> args = new java.util.HashMap<>();
        args.put("x-max-priority", 10); // Priority queue

        channel.queueDeclare(TASK_QUEUE, true, false, false, args);

        logger.info("🔧 Work queue dinleniyor... Çıkmak için CTRL+C");

        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            try {
                String message = new String(delivery.getBody(), "UTF-8");

                // JSON parse et
                @SuppressWarnings("unchecked")
                Map<String, Object> taskData = objectMapper.readValue(message, Map.class);

                // Task'ı işle
                boolean success = processTask(taskData, delivery.getProperties());

                if (success) {
                    // Başarılı işlem - acknowledge
                    channel.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
                    logger.info("✅ Task tamamlandı: {}", taskData.get("task"));
                } else {
                    // İşlem başarısız - reject ve requeue
                    channel.basicNack(delivery.getEnvelope().getDeliveryTag(), false, true);
                    logger.warn("⚠️ Task başarısız, yeniden kuyruğa alındı: {}", taskData.get("task"));
                }

            } catch (Exception e) {
                logger.error("❌ Task işleme hatası", e);
                try {
                    // Exception durumunda message'ı reject et
                    channel.basicNack(delivery.getEnvelope().getDeliveryTag(), false, false);
                } catch (IOException ioException) {
                    logger.error("❌ Message reject hatası", ioException);
                }
            }
        };

        CancelCallback cancelCallback = consumerTag -> {
            logger.info("⚠️ Worker consumer iptal edildi: {}", consumerTag);
        };

        // Consumer'ı başlat (manual ack)
        this.consumerTag = channel.basicConsume(TASK_QUEUE, false, deliverCallback, cancelCallback);
    }

    /**
     * Fanout exchange consumer - Log mesajları
     * 
     * Her consumer kendi queue'suna bind olur ve tüm log mesajlarını alır
     */
    public void consumeLogMessages(String consumerName) throws IOException {
        // Fanout exchange declare et
        channel.exchangeDeclare(LOGS_EXCHANGE, BuiltinExchangeType.FANOUT, true);

        // Geçici queue oluştur (exclusive ve auto-delete)
        String queueName = channel.queueDeclare("", false, true, true, null).getQueue();

        // Queue'yu exchange'e bind et
        channel.queueBind(queueName, LOGS_EXCHANGE, "");

        logger.info("📝 [{}] Log mesajları dinleniyor... Çıkmak için CTRL+C", consumerName);

        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            try {
                String message = new String(delivery.getBody(), "UTF-8");

                // JSON parse et
                @SuppressWarnings("unchecked")
                Map<String, Object> logData = objectMapper.readValue(message, Map.class);

                // Log mesajını işle
                processLogMessage(consumerName, logData, delivery.getProperties());

            } catch (Exception e) {
                logger.error("❌ Log mesajı işleme hatası", e);
            }
        };

        CancelCallback cancelCallback = consumerTag -> {
            logger.info("⚠️ Log consumer [{}] iptal edildi: {}", consumerName, consumerTag);
        };

        // Consumer'ı başlat (auto-ack for logs)
        this.consumerTag = channel.basicConsume(queueName, true, deliverCallback, cancelCallback);
    }

    /**
     * Priority aware consumer - Öncelik sırasına göre task işleme
     */
    public void consumeWithPriority() throws IOException {
        Map<String, Object> args = new java.util.HashMap<>();
        args.put("x-max-priority", 10);

        channel.queueDeclare(TASK_QUEUE, true, false, false, args);

        logger.info("⭐ Priority queue dinleniyor... Çıkmak için CTRL+C");

        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            try {
                String message = new String(delivery.getBody(), "UTF-8");

                @SuppressWarnings("unchecked")
                Map<String, Object> taskData = objectMapper.readValue(message, Map.class);

                // Priority bilgisini al
                Integer priority = delivery.getProperties().getPriority();
                if (priority == null)
                    priority = 0;

                logger.info("⭐ Priority {} task alındı: {}", priority, taskData.get("task"));

                // Priority'ye göre işlem süresi simüle et
                simulateTaskProcessing(priority);

                // Task'ı işle
                boolean success = processTask(taskData, delivery.getProperties());

                if (success) {
                    channel.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
                    logger.info("✅ Priority {} task tamamlandı", priority);
                } else {
                    channel.basicNack(delivery.getEnvelope().getDeliveryTag(), false, true);
                    logger.warn("⚠️ Priority {} task başarısız", priority);
                }

            } catch (Exception e) {
                logger.error("❌ Priority task işleme hatası", e);
                try {
                    channel.basicNack(delivery.getEnvelope().getDeliveryTag(), false, false);
                } catch (IOException ioException) {
                    logger.error("❌ Priority task reject hatası", ioException);
                }
            }
        };

        CancelCallback cancelCallback = consumerTag -> {
            logger.info("⚠️ Priority consumer iptal edildi: {}", consumerTag);
        };

        this.consumerTag = channel.basicConsume(TASK_QUEUE, false, deliverCallback, cancelCallback);
    }

    /**
     * Basit mesaj işleme business logic'i
     */
    private void processSimpleMessage(Map<String, Object> messageData, AMQP.BasicProperties properties) {
        String message = (String) messageData.get("message");
        String timestamp = (String) messageData.get("timestamp");
        String sender = (String) messageData.get("sender");

        logger.info("📨 Mesaj: '{}' (Gönderen: {}, Zaman: {})", message, sender, timestamp);

        // Business logic simülasyonu
        try {
            Thread.sleep(500); // 500ms işlem süresi
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    /**
     * Task işleme business logic'i
     */
    private boolean processTask(Map<String, Object> taskData, AMQP.BasicProperties properties) {
        String task = (String) taskData.get("task");
        Integer priority = (Integer) taskData.get("priority");
        String timestamp = (String) taskData.get("timestamp");

        logger.info("🔧 Task işleniyor: '{}' (Priority: {}, Zaman: {})", task, priority, timestamp);

        try {
            // Task süresini priority'ye göre belirle
            int processingTime = calculateProcessingTime(task, priority);
            Thread.sleep(processingTime);

            // %90 başarı oranı simülasyonu
            boolean success = Math.random() > 0.1;

            if (success) {
                logger.info("✅ Task başarıyla tamamlandı: {}", task);
            } else {
                logger.warn("❌ Task başarısız: {}", task);
            }

            return success;

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }

    /**
     * Log mesajı işleme
     */
    private void processLogMessage(String consumerName, Map<String, Object> logData, AMQP.BasicProperties properties) {
        String level = (String) logData.get("level");
        String message = (String) logData.get("message");
        String timestamp = (String) logData.get("timestamp");
        String source = (String) logData.get("source");

        // Log level'a göre farklı işlem
        String emoji = getLogEmoji(level);

        logger.info("{} [{}] {} - {} (Kaynak: {}, Zaman: {})",
                emoji, consumerName, level, message, source, timestamp);

        // Critical log'lar için özel işlem
        if ("ERROR".equals(level)) {
            logger.warn("🚨 [{}] CRITICAL LOG detected: {}", consumerName, message);
        }
    }

    /**
     * Task işlem süresini hesapla
     */
    private int calculateProcessingTime(String task, Integer priority) {
        // Base time: task uzunluğuna göre
        int baseTime = Math.min(task.length() * 10, 3000); // Max 3 saniye

        // Priority modifier: yüksek priority = hızlı işlem
        double priorityModifier = priority != null ? (11 - priority) / 10.0 : 1.0;

        return (int) (baseTime * priorityModifier);
    }

    /**
     * Priority'ye göre task işlem simülasyonu
     */
    private void simulateTaskProcessing(int priority) throws InterruptedException {
        // Yüksek priority = kısa bekleme
        int waitTime = (10 - priority) * 100; // 100ms - 900ms arası
        Thread.sleep(waitTime);
    }

    /**
     * Log level'a göre emoji
     */
    private String getLogEmoji(String level) {
        switch (level.toUpperCase()) {
            case "ERROR":
                return "❌";
            case "WARN":
                return "⚠️";
            case "INFO":
                return "ℹ️";
            case "DEBUG":
                return "🐛";
            default:
                return "📝";
        }
    }

    /**
     * Consumer'ı durdur
     */
    public void stopConsumer() throws IOException {
        if (consumerTag != null && channel != null && channel.isOpen()) {
            channel.basicCancel(consumerTag);
            logger.info("🛑 Consumer durduruldu");
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
     * Graceful shutdown hook
     */
    private void setupShutdownHook() {
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try {
                logger.info("🛑 Graceful shutdown başlatılıyor...");
                stopConsumer();
                close();
                logger.info("✅ Graceful shutdown tamamlandı");
            } catch (Exception e) {
                logger.error("❌ Shutdown hatası", e);
            }
        }));
    }

    /**
     * Consumer mode selection
     */
    public void runConsumer(String mode, String consumerName) throws IOException {
        setupShutdownHook();

        switch (mode.toLowerCase()) {
            case "simple":
                consumeSimpleMessages();
                break;
            case "work":
                consumeWorkQueue();
                break;
            case "logs":
                consumeLogMessages(consumerName != null ? consumerName : "default");
                break;
            case "priority":
                consumeWithPriority();
                break;
            default:
                logger.error("❌ Bilinmeyen mode: {}", mode);
                return;
        }

        // Consumer çalışır durumda tutulan loop
        try {
            while (true) {
                Thread.sleep(1000);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            logger.info("⚠️ Consumer interrupted");
        }
    }

    /**
     * Main method
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java SimpleConsumer <mode> [consumer-name]");
            System.out.println("Modes:");
            System.out.println("  simple   - Basit queue consumer");
            System.out.println("  work     - Work queue consumer (manual ack)");
            System.out.println("  logs     - Fanout exchange consumer");
            System.out.println("  priority - Priority queue consumer");
            return;
        }

        String mode = args[0];
        String consumerName = args.length > 1 ? args[1] : null;

        SimpleConsumer consumer = new SimpleConsumer();

        try {
            // Bağlan
            consumer.connect();

            logger.info("🚀 RabbitMQ Consumer başlatılıyor - Mode: {}", mode);

            // Consumer'ı çalıştır
            consumer.runConsumer(mode, consumerName);

        } catch (Exception e) {
            logger.error("❌ Consumer hatası", e);
        } finally {
            try {
                consumer.close();
            } catch (Exception e) {
                logger.error("❌ Bağlantı kapatma hatası", e);
            }
        }
    }
}