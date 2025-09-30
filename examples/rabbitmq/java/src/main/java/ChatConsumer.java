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
 * RabbitMQ Chat Consumer - Real-time Chat Uygulaması
 * 
 * Bu sınıf topic exchange kullanarak farklı chat odalarından
 * mesaj alma işlemlerini gösterir. Routing pattern'leri ile
 * istenilen mesaj tiplerini filtreleyebilir.
 */
public class ChatConsumer {

    private static final Logger logger = LoggerFactory.getLogger(ChatConsumer.class);

    // RabbitMQ connection parameters
    private static final String HOST = "localhost";
    private static final int PORT = 5672;
    private static final String USERNAME = "admin";
    private static final String PASSWORD = "admin123";

    // Chat exchange and patterns
    private static final String CHAT_EXCHANGE = "chat_exchange";
    private static final String PRIVATE_EXCHANGE = "private_messages";
    private static final String SYSTEM_EXCHANGE = "system_notifications";

    private Connection connection;
    private Channel channel;
    private ObjectMapper objectMapper;
    private String username;
    private String[] rooms;

    public ChatConsumer(String username, String[] rooms) {
        this.username = username;
        this.rooms = rooms;
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
    }

    /**
     * RabbitMQ bağlantısı oluştur ve exchange'leri hazırla
     */
    public void connect() throws IOException, TimeoutException {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost(HOST);
        factory.setPort(PORT);
        factory.setUsername(USERNAME);
        factory.setPassword(PASSWORD);

        // Consumer için özel ayarlar
        factory.setAutomaticRecoveryEnabled(true);
        factory.setNetworkRecoveryInterval(10000);

        try {
            connection = factory.newConnection();
            channel = connection.createChannel();

            // Prefetch ayarı - her seferinde tek mesaj al
            channel.basicQos(1);

            // Exchange'leri declare et (idempotent)
            setupExchanges();

            logger.info("✅ [{}] RabbitMQ chat sistemine bağlandı", username);
        } catch (IOException | TimeoutException e) {
            logger.error("❌ RabbitMQ bağlantı hatası", e);
            throw e;
        }
    }

    /**
     * Chat sisteminin gerekli exchange'lerini oluştur
     */
    private void setupExchanges() throws IOException {
        // Ana chat exchange - topic type
        channel.exchangeDeclare(CHAT_EXCHANGE, BuiltinExchangeType.TOPIC, true);

        // Private mesajlar için direct exchange
        channel.exchangeDeclare(PRIVATE_EXCHANGE, BuiltinExchangeType.DIRECT, true);

        // Sistem bildirimleri için fanout exchange
        channel.exchangeDeclare(SYSTEM_EXCHANGE, BuiltinExchangeType.FANOUT, true);

        logger.info("📡 [{}] Chat exchange'leri hazırlandı", username);
    }

    /**
     * Oda mesajlarını dinle
     * Routing pattern: "room.<odaadi>.message"
     */
    private void setupRoomConsumers() throws IOException {
        // Her oda için ayrı queue ve binding
        for (String room : rooms) {
            String queueName = "chat_" + username + "_" + room;
            String routingPattern = "room." + room + ".message";

            // Durable queue oluştur
            channel.queueDeclare(queueName, true, false, false, null);

            // Queue'yu chat exchange'ine bind et
            channel.queueBind(queueName, CHAT_EXCHANGE, routingPattern);

            // Consumer callback
            DeliverCallback deliverCallback = (consumerTag, delivery) -> {
                try {
                    String message = new String(delivery.getBody(), "UTF-8");

                    @SuppressWarnings("unchecked")
                    Map<String, Object> chatMessage = objectMapper.readValue(message, Map.class);

                    processRoomMessage(room, chatMessage, delivery.getProperties());

                } catch (Exception e) {
                    logger.error("❌ [{}] Oda mesajı işleme hatası: {}", username, e.getMessage());
                }
            };

            CancelCallback cancelCallback = consumerTag -> {
                logger.info("⚠️ [{}] Oda consumer iptal edildi: {}", username, room);
            };

            // Consumer'ı başlat
            channel.basicConsume(queueName, true, deliverCallback, cancelCallback);

            logger.info("🏠 [{}] Oda dinleniyor: {}", username, room);
        }
    }

    /**
     * Private mesajları dinle
     * Routing key: "user.<username>"
     */
    private void setupPrivateConsumer() throws IOException {
        String queueName = "private_" + username;
        String routingKey = "user." + username;

        // Private queue oluştur
        channel.queueDeclare(queueName, true, false, false, null);

        // Queue'yu private exchange'ine bind et
        channel.queueBind(queueName, PRIVATE_EXCHANGE, routingKey);

        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            try {
                String message = new String(delivery.getBody(), "UTF-8");

                @SuppressWarnings("unchecked")
                Map<String, Object> privateMessage = objectMapper.readValue(message, Map.class);

                processPrivateMessage(privateMessage, delivery.getProperties());

            } catch (Exception e) {
                logger.error("❌ [{}] Private mesaj işleme hatası: {}", username, e.getMessage());
            }
        };

        CancelCallback cancelCallback = consumerTag -> {
            logger.info("⚠️ [{}] Private consumer iptal edildi", username);
        };

        channel.basicConsume(queueName, true, deliverCallback, cancelCallback);

        logger.info("📩 [{}] Private mesajlar dinleniyor", username);
    }

    /**
     * Sistem bildirimlerini dinle
     */
    private void setupSystemConsumer() throws IOException {
        String queueName = "system_" + username;

        // Geçici queue oluştur
        channel.queueDeclare(queueName, false, true, true, null);

        // Queue'yu system exchange'ine bind et
        channel.queueBind(queueName, SYSTEM_EXCHANGE, "");

        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            try {
                String message = new String(delivery.getBody(), "UTF-8");

                @SuppressWarnings("unchecked")
                Map<String, Object> systemMessage = objectMapper.readValue(message, Map.class);

                processSystemMessage(systemMessage, delivery.getProperties());

            } catch (Exception e) {
                logger.error("❌ [{}] Sistem mesajı işleme hatası: {}", username, e.getMessage());
            }
        };

        CancelCallback cancelCallback = consumerTag -> {
            logger.info("⚠️ [{}] System consumer iptal edildi", username);
        };

        channel.basicConsume(queueName, true, deliverCallback, cancelCallback);

        logger.info("📢 [{}] Sistem bildirimleri dinleniyor", username);
    }

    /**
     * Durum güncellemelerini dinle
     * Routing pattern: "status.*"
     */
    private void setupStatusConsumer() throws IOException {
        String queueName = "status_" + username;

        // Geçici queue oluştur
        channel.queueDeclare(queueName, false, true, true, null);

        // Tüm status mesajlarını dinle
        channel.queueBind(queueName, CHAT_EXCHANGE, "status.*");

        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            try {
                String message = new String(delivery.getBody(), "UTF-8");

                @SuppressWarnings("unchecked")
                Map<String, Object> statusMessage = objectMapper.readValue(message, Map.class);

                processStatusMessage(statusMessage, delivery.getProperties());

            } catch (Exception e) {
                logger.error("❌ [{}] Status mesajı işleme hatası: {}", username, e.getMessage());
            }
        };

        CancelCallback cancelCallback = consumerTag -> {
            logger.info("⚠️ [{}] Status consumer iptal edildi", username);
        };

        channel.basicConsume(queueName, true, deliverCallback, cancelCallback);

        logger.info("📊 [{}] Durum güncellemeleri dinleniyor", username);
    }

    /**
     * Oda mesajı işleme
     */
    private void processRoomMessage(String room, Map<String, Object> message, AMQP.BasicProperties properties) {
        String content = (String) message.get("content");
        String sender = (String) message.get("sender");
        String timestamp = (String) message.get("timestamp");
        String messageId = (String) message.get("messageId");

        // Kendi mesajlarını filtrele
        if (!sender.equals(username)) {
            String shortTimestamp = timestamp.substring(11, 19); // HH:mm:ss format
            System.out.printf("💬 [%s] %s (%s): %s%n", room, sender, shortTimestamp, content);

            // Önemli mesajlar için özel işlem
            if (content.toLowerCase().contains("@" + username.toLowerCase())) {
                System.out.printf("🔔 [%s] %s sizi etiketledi!%n", room, sender);
            }
        }
    }

    /**
     * Private mesaj işleme
     */
    private void processPrivateMessage(Map<String, Object> message, AMQP.BasicProperties properties) {
        String content = (String) message.get("content");
        String sender = (String) message.get("sender");
        String timestamp = (String) message.get("timestamp");

        String shortTimestamp = timestamp.substring(11, 19);
        System.out.printf("📩 [PM] %s (%s): %s%n", sender, shortTimestamp, content);

        // PM bildirimi
        System.out.printf("🔔 Yeni özel mesaj: %s%n", sender);
    }

    /**
     * Sistem mesajı işleme
     */
    private void processSystemMessage(Map<String, Object> message, AMQP.BasicProperties properties) {
        String content = (String) message.get("content");
        String sender = (String) message.get("sender");
        String timestamp = (String) message.get("timestamp");

        String shortTimestamp = timestamp.substring(11, 19);
        System.out.printf("📢 [SYSTEM] %s (%s): %s%n", sender, shortTimestamp, content);
    }

    /**
     * Durum mesajı işleme
     */
    private void processStatusMessage(Map<String, Object> message, AMQP.BasicProperties properties) {
        String statusUser = (String) message.get("username");
        String status = (String) message.get("status");
        String room = (String) message.get("room");

        // Kendi status mesajlarını filtrele
        if (!statusUser.equals(username)) {
            String emoji = getStatusEmoji(status);
            System.out.printf("📊 %s %s - %s%n", emoji, statusUser, getStatusMessage(status, room));
        }
    }

    /**
     * Status emoji'si
     */
    private String getStatusEmoji(String status) {
        switch (status.toUpperCase()) {
            case "JOIN":
                return "✅";
            case "LEAVE":
                return "❌";
            case "TYPING":
                return "⌨️";
            case "IDLE":
                return "💤";
            default:
                return "📊";
        }
    }

    /**
     * Status mesajı
     */
    private String getStatusMessage(String status, String room) {
        switch (status.toUpperCase()) {
            case "JOIN":
                return "odaya katıldı: " + room;
            case "LEAVE":
                return "odadan ayrıldı: " + room;
            case "TYPING":
                return "yazıyor... (" + room + ")";
            case "IDLE":
                return "uzakta";
            default:
                return "durumu güncellendi";
        }
    }

    /**
     * Tüm consumer'ları başlat
     */
    public void startListening() throws IOException {
        logger.info("🚀 [{}] Chat consumer başlatılıyor...", username);

        // Farklı mesaj tiplerini dinle
        setupRoomConsumers();
        setupPrivateConsumer();
        setupSystemConsumer();
        setupStatusConsumer();

        logger.info("👂 [{}] Tüm chat kanalları dinleniyor", username);

        // Kullanıcı bilgisi
        System.out.println("\n💬 Chat Consumer - " + username);
        System.out.println("====================================");
        System.out.println("Dinlenen odalar: " + String.join(", ", rooms));
        System.out.println("Private mesajlar: Aktif");
        System.out.println("Sistem bildirimleri: Aktif");
        System.out.println("Durum güncellemeleri: Aktif");
        System.out.println("\nMesajlar aşağıda görünecek...");
        System.out.println("Çıkmak için CTRL+C kullanın");
        System.out.println("====================================\n");
    }

    /**
     * Graceful shutdown
     */
    private void setupShutdownHook() {
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try {
                logger.info("🛑 [{}] Graceful shutdown başlatılıyor...", username);
                close();
                logger.info("✅ [{}] Graceful shutdown tamamlandı", username);
            } catch (Exception e) {
                logger.error("❌ [{}] Shutdown hatası", username, e);
            }
        }));
    }

    /**
     * Chat consumer'ı çalıştır
     */
    public void run() throws IOException {
        setupShutdownHook();
        startListening();

        // Consumer'ı çalışır durumda tut
        try {
            while (true) {
                Thread.sleep(1000);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            logger.info("⚠️ [{}] Consumer interrupted", username);
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
        logger.info("🔒 [{}] Chat bağlantısı kapatıldı", username);
    }

    /**
     * Main method
     */
    public static void main(String[] args) {
        if (args.length < 2) {
            System.out.println("Usage: java ChatConsumer <username> <room1,room2,room3>");
            System.out.println("Örnek: java ChatConsumer alice general,tech,random");
            return;
        }

        String username = args[0];
        String[] rooms = args[1].split(",");

        // Room isimlerini temizle
        for (int i = 0; i < rooms.length; i++) {
            rooms[i] = rooms[i].trim();
        }

        ChatConsumer chatConsumer = new ChatConsumer(username, rooms);

        try {
            // Bağlan
            chatConsumer.connect();

            // Consumer'ı çalıştır
            chatConsumer.run();

        } catch (Exception e) {
            logger.error("❌ [{}] Chat consumer hatası", username, e);
        } finally {
            try {
                chatConsumer.close();
            } catch (Exception e) {
                logger.error("❌ [{}] Bağlantı kapatma hatası", username, e);
            }
        }
    }
}