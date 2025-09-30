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
import java.util.Scanner;
import java.util.concurrent.TimeoutException;

/**
 * RabbitMQ Chat Producer - Real-time Chat Uygulaması
 * 
 * Bu sınıf topic exchange kullanarak chat odalarına mesaj gönderme
 * işlemlerini gösterir. Farklı routing key'ler ile farklı odalara
 * mesaj gönderebilir.
 */
public class ChatProducer {

    private static final Logger logger = LoggerFactory.getLogger(ChatProducer.class);

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

    public ChatProducer(String username) {
        this.username = username;
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

        try {
            connection = factory.newConnection();
            channel = connection.createChannel();

            // Chat exchange'lerini declare et
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

        logger.info("📡 Chat exchange'leri hazırlandı");
    }

    /**
     * Genel chat odasına mesaj gönder
     * Routing key format: "room.<odaadi>.message"
     */
    public void sendRoomMessage(String room, String message) throws IOException {
        String routingKey = "room." + room + ".message";

        Map<String, Object> messageData = createChatMessage("ROOM", message, room, null);

        sendChatMessage(CHAT_EXCHANGE, routingKey, messageData);

        logger.info("💬 [{}] Oda mesajı gönderildi: {} -> '{}'", username, room, message);
    }

    /**
     * Private mesaj gönder
     * Routing key format: "user.<hedefuser>"
     */
    public void sendPrivateMessage(String targetUser, String message) throws IOException {
        String routingKey = "user." + targetUser;

        Map<String, Object> messageData = createChatMessage("PRIVATE", message, null, targetUser);

        sendChatMessage(PRIVATE_EXCHANGE, routingKey, messageData);

        logger.info("📩 [{}] Özel mesaj gönderildi: {} -> '{}'", username, targetUser, message);
    }

    /**
     * Sistem bildirimi gönder (tüm kullanıcılara)
     */
    public void sendSystemNotification(String notification) throws IOException {
        Map<String, Object> messageData = createChatMessage("SYSTEM", notification, null, null);

        sendChatMessage(SYSTEM_EXCHANGE, "", messageData);

        logger.info("📢 [{}] Sistem bildirimi gönderildi: '{}'", username, notification);
    }

    /**
     * Kullanıcı durumu bildirimi (join/leave)
     * Routing key format: "status.<durum>"
     */
    public void sendStatusUpdate(String status, String room) throws IOException {
        String routingKey = "status." + status;

        Map<String, Object> statusData = new HashMap<>();
        statusData.put("type", "STATUS");
        statusData.put("username", username);
        statusData.put("status", status.toUpperCase()); // JOIN, LEAVE, TYPING, IDLE
        statusData.put("room", room);
        statusData.put("timestamp", LocalDateTime.now().toString());

        sendChatMessage(CHAT_EXCHANGE, routingKey, statusData);

        logger.info("📊 [{}] Durum güncellendi: {} -> {}", username, status, room);
    }

    /**
     * Chat mesajı template'i oluştur
     */
    private Map<String, Object> createChatMessage(String type, String content, String room, String targetUser) {
        Map<String, Object> message = new HashMap<>();
        message.put("type", type);
        message.put("content", content);
        message.put("sender", username);
        message.put("timestamp", LocalDateTime.now().toString());
        message.put("messageId", generateMessageId());

        if (room != null) {
            message.put("room", room);
        }

        if (targetUser != null) {
            message.put("targetUser", targetUser);
        }

        // Mesaj metadata'sı
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("clientVersion", "1.0.0");
        metadata.put("platform", "Java");
        metadata.put("messageLength", content.length());
        message.put("metadata", metadata);

        return message;
    }

    /**
     * Chat mesajını exchange'e gönder
     */
    private void sendChatMessage(String exchange, String routingKey, Map<String, Object> messageData)
            throws IOException {
        try {
            String jsonMessage = objectMapper.writeValueAsString(messageData);

            // Message properties
            AMQP.BasicProperties properties = new AMQP.BasicProperties.Builder()
                    .contentType("application/json")
                    .deliveryMode(1) // Non-persistent for chat (performance)
                    .timestamp(new java.util.Date())
                    .messageId((String) messageData.get("messageId"))
                    .userId(username)
                    .headers(createMessageHeaders(messageData))
                    .build();

            channel.basicPublish(exchange, routingKey, properties, jsonMessage.getBytes("UTF-8"));

        } catch (Exception e) {
            logger.error("❌ Chat mesajı gönderme hatası", e);
            throw new IOException("Chat message sending failed", e);
        }
    }

    /**
     * Mesaj header'larını oluştur
     */
    private Map<String, Object> createMessageHeaders(Map<String, Object> messageData) {
        Map<String, Object> headers = new HashMap<>();
        headers.put("messageType", messageData.get("type"));
        headers.put("sender", messageData.get("sender"));
        headers.put("chatVersion", "2.0");

        if (messageData.containsKey("room")) {
            headers.put("room", messageData.get("room"));
        }

        return headers;
    }

    /**
     * Benzersiz mesaj ID oluştur
     */
    private String generateMessageId() {
        return username + "_" + System.currentTimeMillis() + "_" + Math.random();
    }

    /**
     * Batch mesaj gönderme (test amaçlı)
     */
    public void sendBatchMessages(String room, int count) throws IOException {
        logger.info("📦 [{}] Batch mesaj gönderiliyor: {} adet -> {}", username, count, room);

        long startTime = System.currentTimeMillis();

        for (int i = 1; i <= count; i++) {
            String message = String.format("Batch mesaj #%d from %s", i, username);
            sendRoomMessage(room, message);

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

        logger.info("✅ [{}] Batch tamamlandı: {} mesaj, {} ms, {:.2f} msg/sec",
                username, count, duration, messagesPerSecond);
    }

    /**
     * Interactive chat CLI
     */
    public void startInteractiveChat() {
        Scanner scanner = new Scanner(System.in);

        System.out.println("\n💬 RabbitMQ Chat - " + username);
        System.out.println("====================================");
        System.out.println("Komutlar:");
        System.out.println("  /room <oda> <mesaj>     - Oda mesajı gönder");
        System.out.println("  /pm <kullanıcı> <mesaj> - Özel mesaj gönder");
        System.out.println("  /join <oda>             - Odaya katıl");
        System.out.println("  /leave <oda>            - Odadan ayrıl");
        System.out.println("  /system <bildirim>      - Sistem bildirimi");
        System.out.println("  /batch <oda> <sayı>     - Batch mesaj test");
        System.out.println("  /status                 - Durum göster");
        System.out.println("  /quit                   - Çıkış");
        System.out.println();

        String currentRoom = "general";
        System.out.println("🏠 Varsayılan oda: " + currentRoom);

        try {
            // İlk katılım bildirimi
            sendStatusUpdate("join", currentRoom);

            while (true) {
                System.out.print("[" + username + "@" + currentRoom + "] > ");
                String input = scanner.nextLine().trim();

                if (input.isEmpty()) {
                    continue;
                }

                if (input.equalsIgnoreCase("/quit") || input.equalsIgnoreCase("/exit")) {
                    sendStatusUpdate("leave", currentRoom);
                    break;
                }

                try {
                    if (input.startsWith("/")) {
                        currentRoom = processCommand(input, currentRoom);
                    } else {
                        // Normal mesaj - mevcut odaya gönder
                        sendRoomMessage(currentRoom, input);
                    }
                } catch (Exception e) {
                    logger.error("❌ Komut işleme hatası: {}", e.getMessage());
                }
            }

        } catch (Exception e) {
            logger.error("❌ Chat session hatası", e);
        } finally {
            scanner.close();
        }
    }

    /**
     * Chat komutlarını işle
     */
    private String processCommand(String input, String currentRoom) throws IOException {
        String[] parts = input.split("\\s+", 3);
        String command = parts[0].toLowerCase();

        switch (command) {
            case "/room":
                if (parts.length >= 3) {
                    String room = parts[1];
                    String message = input.substring(input.indexOf(parts[2]));
                    sendRoomMessage(room, message);
                } else {
                    System.out.println("❌ Format: /room <oda> <mesaj>");
                }
                break;

            case "/pm":
                if (parts.length >= 3) {
                    String targetUser = parts[1];
                    String message = input.substring(input.indexOf(parts[2]));
                    sendPrivateMessage(targetUser, message);
                } else {
                    System.out.println("❌ Format: /pm <kullanıcı> <mesaj>");
                }
                break;

            case "/join":
                if (parts.length >= 2) {
                    String newRoom = parts[1];
                    sendStatusUpdate("leave", currentRoom);
                    sendStatusUpdate("join", newRoom);
                    System.out.println("🏠 Oda değiştirildi: " + currentRoom + " -> " + newRoom);
                    return newRoom;
                } else {
                    System.out.println("❌ Format: /join <oda>");
                }
                break;

            case "/leave":
                if (parts.length >= 2) {
                    String leaveRoom = parts[1];
                    sendStatusUpdate("leave", leaveRoom);
                    if (leaveRoom.equals(currentRoom)) {
                        String newRoom = "general";
                        sendStatusUpdate("join", newRoom);
                        System.out.println("🏠 Oda değiştirildi: " + currentRoom + " -> " + newRoom);
                        return newRoom;
                    }
                } else {
                    System.out.println("❌ Format: /leave <oda>");
                }
                break;

            case "/system":
                if (parts.length >= 2) {
                    String notification = input.substring(input.indexOf(parts[1]));
                    sendSystemNotification(notification);
                } else {
                    System.out.println("❌ Format: /system <bildirim>");
                }
                break;

            case "/batch":
                if (parts.length >= 3) {
                    try {
                        String room = parts[1];
                        int count = Integer.parseInt(parts[2]);
                        if (count > 0 && count <= 1000) {
                            sendBatchMessages(room, count);
                        } else {
                            System.out.println("❌ Sayı 1-1000 arasında olmalı");
                        }
                    } catch (NumberFormatException e) {
                        System.out.println("❌ Geçersiz sayı");
                    }
                } else {
                    System.out.println("❌ Format: /batch <oda> <sayı>");
                }
                break;

            case "/status":
                System.out.println("📊 Kullanıcı: " + username);
                System.out.println("📊 Mevcut oda: " + currentRoom);
                System.out.println("📊 Bağlantı: " + (connection.isOpen() ? "Aktif" : "Kapalı"));
                break;

            default:
                System.out.println("❌ Bilinmeyen komut: " + command);
        }

        return currentRoom;
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
        if (args.length < 1) {
            System.out.println("Usage: java ChatProducer <username>");
            return;
        }

        String username = args[0];
        ChatProducer chatProducer = new ChatProducer(username);

        try {
            // Bağlan
            chatProducer.connect();

            // Interactive chat başlat
            chatProducer.startInteractiveChat();

        } catch (Exception e) {
            logger.error("❌ Chat producer hatası", e);
        } finally {
            try {
                chatProducer.close();
            } catch (Exception e) {
                logger.error("❌ Bağlantı kapatma hatası", e);
            }
        }
    }
}