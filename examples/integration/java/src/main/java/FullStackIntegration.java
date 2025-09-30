package main.java;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.serialization.StringSerializer;
import org.apache.kafka.common.serialization.StringDeserializer;

import com.rabbitmq.client.*;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch.core.IndexRequest;
import co.elastic.clients.elasticsearch.core.SearchRequest;
import co.elastic.clients.elasticsearch.core.SearchResponse;
import co.elastic.clients.json.jackson.JacksonJsonpMapper;
import co.elastic.clients.transport.ElasticsearchTransport;
import co.elastic.clients.transport.rest_client.RestClientTransport;
import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.LocalDateTime;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;

/**
 * Full Stack Integration Demo - Tüm Teknolojilerin Entegrasyonu
 * 
 * Bu örnek Kafka, RabbitMQ, Redis ve Elasticsearch'ün birlikte nasıl
 * çalıştığını
 * kapsamlı bir e-ticaret platformu simülasyonu ile gösterir:
 * 
 * Mimari Akış:
 * 1. KAFKA: Event streaming ve order processing
 * 2. RABBITMQ: Real-time notifications ve messaging
 * 3. REDIS: Caching, session management ve real-time analytics
 * 4. ELASTICSEARCH: Product search, analytics ve logging
 * 
 * @author: Senior Software Architect
 * @version: 1.0
 */
public class FullStackIntegration {

    // Kafka configuration
    private KafkaProducer<String, String> kafkaProducer;
    private KafkaConsumer<String, String> kafkaConsumer;
    private static final String KAFKA_TOPIC_ORDERS = "ecommerce-orders";
    private static final String KAFKA_TOPIC_EVENTS = "user-events";

    // RabbitMQ configuration
    private Connection rabbitConnection;
    private Channel rabbitChannel;
    private static final String RABBITMQ_QUEUE_NOTIFICATIONS = "notifications";
    private static final String RABBITMQ_EXCHANGE_EVENTS = "events.exchange";

    // Redis configuration
    private Jedis redis;
    private static final String REDIS_PREFIX = "ecommerce:";

    // Elasticsearch configuration
    private ElasticsearchClient esClient;
    private static final String ES_INDEX_PRODUCTS = "products";
    private static final String ES_INDEX_LOGS = "application_logs";

    private ObjectMapper objectMapper = new ObjectMapper();
    private boolean isRunning = true;

    /**
     * Order Event Model
     */
    public static class OrderEvent {
        @JsonProperty("orderId")
        private String orderId;

        @JsonProperty("userId")
        private String userId;

        @JsonProperty("productId")
        private String productId;

        @JsonProperty("productName")
        private String productName;

        @JsonProperty("quantity")
        private int quantity;

        @JsonProperty("price")
        private double price;

        @JsonProperty("status")
        private String status; // created, processing, shipped, delivered

        @JsonProperty("timestamp")
        private String timestamp;

        public OrderEvent() {
        }

        public OrderEvent(String orderId, String userId, String productId,
                String productName, int quantity, double price, String status) {
            this.orderId = orderId;
            this.userId = userId;
            this.productId = productId;
            this.productName = productName;
            this.quantity = quantity;
            this.price = price;
            this.status = status;
            this.timestamp = LocalDateTime.now().toString();
        }

        // Getters and Setters
        public String getOrderId() {
            return orderId;
        }

        public void setOrderId(String orderId) {
            this.orderId = orderId;
        }

        public String getUserId() {
            return userId;
        }

        public void setUserId(String userId) {
            this.userId = userId;
        }

        public String getProductId() {
            return productId;
        }

        public void setProductId(String productId) {
            this.productId = productId;
        }

        public String getProductName() {
            return productName;
        }

        public void setProductName(String productName) {
            this.productName = productName;
        }

        public int getQuantity() {
            return quantity;
        }

        public void setQuantity(int quantity) {
            this.quantity = quantity;
        }

        public double getPrice() {
            return price;
        }

        public void setPrice(double price) {
            this.price = price;
        }

        public String getStatus() {
            return status;
        }

        public void setStatus(String status) {
            this.status = status;
        }

        public String getTimestamp() {
            return timestamp;
        }

        public void setTimestamp(String timestamp) {
            this.timestamp = timestamp;
        }
    }

    /**
     * Notification Model
     */
    public static class Notification {
        @JsonProperty("userId")
        private String userId;

        @JsonProperty("type")
        private String type; // order_update, promotion, system

        @JsonProperty("title")
        private String title;

        @JsonProperty("message")
        private String message;

        @JsonProperty("timestamp")
        private String timestamp;

        public Notification() {
        }

        public Notification(String userId, String type, String title, String message) {
            this.userId = userId;
            this.type = type;
            this.title = title;
            this.message = message;
            this.timestamp = LocalDateTime.now().toString();
        }

        // Getters and Setters
        public String getUserId() {
            return userId;
        }

        public void setUserId(String userId) {
            this.userId = userId;
        }

        public String getType() {
            return type;
        }

        public void setType(String type) {
            this.type = type;
        }

        public String getTitle() {
            return title;
        }

        public void setTitle(String title) {
            this.title = title;
        }

        public String getMessage() {
            return message;
        }

        public void setMessage(String message) {
            this.message = message;
        }

        public String getTimestamp() {
            return timestamp;
        }

        public void setTimestamp(String timestamp) {
            this.timestamp = timestamp;
        }
    }

    /**
     * Tüm sistemleri başlatır
     */
    public void initializeAllSystems() {
        System.out.println("=== Full Stack Integration Başlatılıyor ===");

        try {
            // 1. Kafka Producer/Consumer başlat
            initializeKafka();

            // 2. RabbitMQ bağlantısını başlat
            initializeRabbitMQ();

            // 3. Redis bağlantısını başlat
            initializeRedis();

            // 4. Elasticsearch client'ı başlat
            initializeElasticsearch();

            System.out.println("✅ Tüm sistemler başarıyla başlatıldı!");

        } catch (Exception e) {
            System.err.println("❌ Sistem başlatma hatası: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Kafka producer ve consumer'ı başlatır
     */
    private void initializeKafka() {
        System.out.println("🔥 Kafka başlatılıyor...");

        // Producer configuration
        Properties producerProps = new Properties();
        producerProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        producerProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        producerProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        producerProps.put(ProducerConfig.ACKS_CONFIG, "all");
        producerProps.put(ProducerConfig.RETRIES_CONFIG, 3);
        producerProps.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);

        kafkaProducer = new KafkaProducer<>(producerProps);

        // Consumer configuration
        Properties consumerProps = new Properties();
        consumerProps.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        consumerProps.put(ConsumerConfig.GROUP_ID_CONFIG, "ecommerce-integration-group");
        consumerProps.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        consumerProps.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        consumerProps.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        consumerProps.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);

        kafkaConsumer = new KafkaConsumer<>(consumerProps);
        kafkaConsumer.subscribe(Arrays.asList(KAFKA_TOPIC_ORDERS, KAFKA_TOPIC_EVENTS));

        System.out.println("✅ Kafka başlatıldı");
    }

    /**
     * RabbitMQ bağlantısını başlatır
     */
    private void initializeRabbitMQ() throws Exception {
        System.out.println("🐰 RabbitMQ başlatılıyor...");

        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        factory.setPort(5672);
        factory.setUsername("guest");
        factory.setPassword("guest");

        rabbitConnection = factory.newConnection();
        rabbitChannel = rabbitConnection.createChannel();

        // Exchange ve queue'ları oluştur
        rabbitChannel.exchangeDeclare(RABBITMQ_EXCHANGE_EVENTS, "topic", true);
        rabbitChannel.queueDeclare(RABBITMQ_QUEUE_NOTIFICATIONS, true, false, false, null);
        rabbitChannel.queueBind(RABBITMQ_QUEUE_NOTIFICATIONS, RABBITMQ_EXCHANGE_EVENTS, "notification.*");

        System.out.println("✅ RabbitMQ başlatıldı");
    }

    /**
     * Redis bağlantısını başlatır
     */
    private void initializeRedis() {
        System.out.println("⚡ Redis başlatılıyor...");

        redis = new Jedis("localhost", 6379);
        redis.ping(); // Bağlantıyı test et

        System.out.println("✅ Redis başlatıldı");
    }

    /**
     * Elasticsearch client'ı başlatır
     */
    private void initializeElasticsearch() throws Exception {
        System.out.println("🔍 Elasticsearch başlatılıyor...");

        RestClient restClient = RestClient.builder(
                new HttpHost("localhost", 9200, "http")).build();

        ElasticsearchTransport transport = new RestClientTransport(
                restClient, new JacksonJsonpMapper());

        esClient = new ElasticsearchClient(transport);

        System.out.println("✅ Elasticsearch başlatıldı");
    }

    /**
     * E-ticaret senaryosunu simüle eder
     */
    public void simulateECommerceScenario() {
        System.out.println("\n=== E-Ticaret Senaryosu Simülasyonu ===");

        try {
            // Consumer thread'ini başlat
            startEventProcessingThread();

            // Order processing simulation
            String[] users = { "user1", "user2", "user3", "user4", "user5" };
            String[] products = { "iphone14", "macbook", "airpods", "watch", "ipad" };
            String[] productNames = { "iPhone 14 Pro", "MacBook Air M2", "AirPods Pro", "Apple Watch", "iPad Pro" };
            double[] prices = { 1299.99, 1199.99, 249.99, 399.99, 799.99 };

            for (int i = 0; i < 10; i++) {
                String orderId = "ORDER-" + (1000 + i);
                String userId = users[i % users.length];
                int productIndex = i % products.length;
                String productId = products[productIndex];
                String productName = productNames[productIndex];
                double price = prices[productIndex];
                int quantity = 1 + (i % 3);

                // 1. Siparişi Kafka'ya gönder
                OrderEvent order = new OrderEvent(orderId, userId, productId, productName, quantity, price, "created");
                publishOrderEvent(order);

                // 2. Kullanıcı session'ını Redis'e kaydet
                updateUserSession(userId, productId, "order_created");

                // 3. Ürün bilgilerini Elasticsearch'e index'le
                indexProductSearch(productId, productName, price);

                // 4. RabbitMQ ile notification gönder
                sendNotification(userId, "order_update", "Sipariş Onaylandı",
                        "Siparişiniz " + orderId + " başarıyla oluşturuldu.");

                System.out.printf("📦 Sipariş %s oluşturuldu (Kullanıcı: %s, Ürün: %s)\n",
                        orderId, userId, productName);

                Thread.sleep(2000); // 2 saniye bekle

                // Sipariş durumunu güncelle
                order.setStatus("processing");
                publishOrderEvent(order);

                sendNotification(userId, "order_update", "Sipariş Hazırlanıyor",
                        "Siparişiniz " + orderId + " hazırlanmaya başlandı.");

                Thread.sleep(1000);
            }

            System.out.println("✅ E-ticaret senaryosu tamamlandı!");

        } catch (Exception e) {
            System.err.println("❌ Senaryo simülasyon hatası: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Kafka'ya order event'i gönderir
     */
    private void publishOrderEvent(OrderEvent order) {
        try {
            String orderJson = objectMapper.writeValueAsString(order);
            ProducerRecord<String, String> record = new ProducerRecord<>(
                    KAFKA_TOPIC_ORDERS, order.getOrderId(), orderJson);

            kafkaProducer.send(record, (metadata, exception) -> {
                if (exception != null) {
                    System.err.println("❌ Kafka gönderim hatası: " + exception.getMessage());
                } else {
                    System.out.printf("✅ Kafka'ya gönderildi: Topic=%s, Partition=%d, Offset=%d\n",
                            metadata.topic(), metadata.partition(), metadata.offset());
                }
            });

        } catch (Exception e) {
            System.err.println("❌ Order event publishing hatası: " + e.getMessage());
        }
    }

    /**
     * RabbitMQ ile notification gönderir
     */
    private void sendNotification(String userId, String type, String title, String message) {
        try {
            Notification notification = new Notification(userId, type, title, message);
            String notificationJson = objectMapper.writeValueAsString(notification);

            rabbitChannel.basicPublish(
                    RABBITMQ_EXCHANGE_EVENTS,
                    "notification." + type,
                    MessageProperties.PERSISTENT_TEXT_PLAIN,
                    notificationJson.getBytes());

            System.out.printf("📢 Notification gönderildi: %s -> %s\n", userId, title);

        } catch (Exception e) {
            System.err.println("❌ Notification gönderim hatası: " + e.getMessage());
        }
    }

    /**
     * Redis'te kullanıcı session'ını günceller
     */
    private void updateUserSession(String userId, String productId, String action) {
        try {
            String sessionKey = REDIS_PREFIX + "session:" + userId;
            String activityKey = REDIS_PREFIX + "activity:" + userId;

            // Session bilgilerini güncelle
            redis.hset(sessionKey, "lastActivity", LocalDateTime.now().toString());
            redis.hset(sessionKey, "lastProduct", productId);
            redis.hset(sessionKey, "lastAction", action);
            redis.expire(sessionKey, 3600); // 1 saat TTL

            // Activity log'u ekle
            redis.lpush(activityKey, action + ":" + productId + ":" + System.currentTimeMillis());
            redis.ltrim(activityKey, 0, 99); // Son 100 activity'yi tut

            // Real-time analytics
            String analyticsKey = REDIS_PREFIX + "analytics:orders:today";
            redis.incr(analyticsKey);
            redis.expire(analyticsKey, 86400); // 24 saat TTL

            System.out.printf("💾 Redis'te güncellendi: %s -> %s\n", userId, action);

        } catch (Exception e) {
            System.err.println("❌ Redis güncelleme hatası: " + e.getMessage());
        }
    }

    /**
     * Elasticsearch'e ürün arama bilgilerini index'ler
     */
    private void indexProductSearch(String productId, String productName, double price) {
        try {
            Map<String, Object> productDoc = new HashMap<>();
            productDoc.put("productId", productId);
            productDoc.put("name", productName);
            productDoc.put("price", price);
            productDoc.put("searchCount", 1);
            productDoc.put("lastSearched", LocalDateTime.now().toString());

            IndexRequest<Map<String, Object>> request = IndexRequest.of(i -> i
                    .index(ES_INDEX_PRODUCTS)
                    .id(productId)
                    .document(productDoc));

            esClient.index(request);

            System.out.printf("🔍 Elasticsearch'e index'lendi: %s\n", productName);

        } catch (Exception e) {
            System.err.println("❌ Elasticsearch indexing hatası: " + e.getMessage());
        }
    }

    /**
     * Event processing thread'ini başlatır
     */
    private void startEventProcessingThread() {
        Thread eventProcessor = new Thread(() -> {
            System.out.println("🔄 Event processing thread başlatıldı");

            while (isRunning) {
                try {
                    ConsumerRecords<String, String> records = kafkaConsumer.poll(Duration.ofMillis(1000));

                    for (ConsumerRecord<String, String> record : records) {
                        processEvent(record);
                    }

                    kafkaConsumer.commitSync();

                } catch (Exception e) {
                    System.err.println("❌ Event processing hatası: " + e.getMessage());
                }
            }
        });

        eventProcessor.setDaemon(true);
        eventProcessor.start();
    }

    /**
     * Gelen event'leri işler
     */
    private void processEvent(ConsumerRecord<String, String> record) {
        try {
            System.out.printf("📨 Event işleniyor: Topic=%s, Key=%s\n",
                    record.topic(), record.key());

            if (KAFKA_TOPIC_ORDERS.equals(record.topic())) {
                OrderEvent order = objectMapper.readValue(record.value(), OrderEvent.class);
                processOrderEvent(order);
            }

            // Application log'unu Elasticsearch'e gönder
            logToElasticsearch("event_processed", record.topic(), record.key());

        } catch (Exception e) {
            System.err.println("❌ Event processing error: " + e.getMessage());
        }
    }

    /**
     * Order event'ini işler
     */
    private void processOrderEvent(OrderEvent order) {
        try {
            System.out.printf("🔄 Order işleniyor: %s (%s)\n", order.getOrderId(), order.getStatus());

            // Order durumuna göre işlem yap
            switch (order.getStatus()) {
                case "created":
                    // Inventory kontrolü simülasyonu
                    updateInventoryCache(order.getProductId(), -order.getQuantity());
                    break;

                case "processing":
                    // Payment processing simülasyonu
                    processPayment(order);
                    break;

                case "shipped":
                    // Shipping notification
                    sendNotification(order.getUserId(), "order_update", "Sipariş Kargoya Verildi",
                            "Siparişiniz " + order.getOrderId() + " kargoya verildi.");
                    break;
            }

            // Order analytics
            updateOrderAnalytics(order);

        } catch (Exception e) {
            System.err.println("❌ Order processing hatası: " + e.getMessage());
        }
    }

    /**
     * Redis'te inventory cache'ini günceller
     */
    private void updateInventoryCache(String productId, int quantityChange) {
        try {
            String inventoryKey = REDIS_PREFIX + "inventory:" + productId;

            if (!redis.exists(inventoryKey)) {
                redis.set(inventoryKey, "100"); // Default inventory
            }

            redis.incrBy(inventoryKey, quantityChange);
            int currentStock = Integer.parseInt(redis.get(inventoryKey));

            System.out.printf("📦 Inventory güncellendi: %s -> %d\n", productId, currentStock);

            // Low stock alert
            if (currentStock < 10) {
                sendLowStockAlert(productId, currentStock);
            }

        } catch (Exception e) {
            System.err.println("❌ Inventory update hatası: " + e.getMessage());
        }
    }

    /**
     * Low stock alert gönderir
     */
    private void sendLowStockAlert(String productId, int currentStock) {
        try {
            Notification alert = new Notification(
                    "admin", "system", "Low Stock Alert",
                    "Product " + productId + " has only " + currentStock + " items left");

            String alertJson = objectMapper.writeValueAsString(alert);

            rabbitChannel.basicPublish(
                    RABBITMQ_EXCHANGE_EVENTS,
                    "notification.system",
                    MessageProperties.PERSISTENT_TEXT_PLAIN,
                    alertJson.getBytes());

            System.out.printf("⚠️ Low stock alert: %s (%d kaldı)\n", productId, currentStock);

        } catch (Exception e) {
            System.err.println("❌ Low stock alert hatası: " + e.getMessage());
        }
    }

    /**
     * Payment processing simülasyonu
     */
    private void processPayment(OrderEvent order) {
        try {
            // Simulated payment processing delay
            Thread.sleep(1000);

            double totalAmount = order.getPrice() * order.getQuantity();

            // Payment bilgilerini Redis'e kaydet
            String paymentKey = REDIS_PREFIX + "payment:" + order.getOrderId();
            Map<String, String> paymentData = new HashMap<>();
            paymentData.put("orderId", order.getOrderId());
            paymentData.put("userId", order.getUserId());
            paymentData.put("amount", String.valueOf(totalAmount));
            paymentData.put("status", "completed");
            paymentData.put("timestamp", LocalDateTime.now().toString());

            redis.hmset(paymentKey, paymentData);
            redis.expire(paymentKey, 86400 * 30); // 30 gün TTL

            System.out.printf("💳 Payment processed: %s -> $%.2f\n", order.getOrderId(), totalAmount);

        } catch (Exception e) {
            System.err.println("❌ Payment processing hatası: " + e.getMessage());
        }
    }

    /**
     * Order analytics günceller
     */
    private void updateOrderAnalytics(OrderEvent order) {
        try {
            String today = LocalDateTime.now().toLocalDate().toString();

            // Daily order count
            String orderCountKey = REDIS_PREFIX + "analytics:orders:" + today;
            redis.incr(orderCountKey);
            redis.expire(orderCountKey, 86400 * 7); // 7 gün TTL

            // Daily revenue
            String revenueKey = REDIS_PREFIX + "analytics:revenue:" + today;
            double orderValue = order.getPrice() * order.getQuantity();
            redis.incrByFloat(revenueKey, orderValue);
            redis.expire(revenueKey, 86400 * 7);

            // Product popularity
            String popularityKey = REDIS_PREFIX + "analytics:popularity:" + order.getProductId();
            redis.incr(popularityKey);
            redis.expire(popularityKey, 86400 * 30); // 30 gün TTL

            System.out.printf("📊 Analytics güncellendi: Order=%s, Revenue=$%.2f\n",
                    order.getOrderId(), orderValue);

        } catch (Exception e) {
            System.err.println("❌ Analytics update hatası: " + e.getMessage());
        }
    }

    /**
     * Application log'unu Elasticsearch'e gönderir
     */
    private void logToElasticsearch(String level, String message, String details) {
        try {
            Map<String, Object> logDoc = new HashMap<>();
            logDoc.put("level", level);
            logDoc.put("message", message);
            logDoc.put("details", details);
            logDoc.put("timestamp", LocalDateTime.now().toString());
            logDoc.put("application", "ecommerce-integration");

            IndexRequest<Map<String, Object>> request = IndexRequest.of(i -> i
                    .index(ES_INDEX_LOGS)
                    .document(logDoc));

            esClient.index(request);

        } catch (Exception e) {
            System.err.println("❌ Elasticsearch logging hatası: " + e.getMessage());
        }
    }

    /**
     * Real-time dashboard metrics'lerini gösterir
     */
    public void showDashboardMetrics() {
        System.out.println("\n=== Real-Time Dashboard Metrikleri ===");

        try {
            String today = LocalDateTime.now().toLocalDate().toString();

            // Order metrics from Redis
            String orderCountKey = REDIS_PREFIX + "analytics:orders:" + today;
            String orderCount = redis.get(orderCountKey);

            String revenueKey = REDIS_PREFIX + "analytics:revenue:" + today;
            String revenue = redis.get(revenueKey);

            System.out.println("📊 Günlük Metrikler:");
            System.out.println("   Toplam Sipariş: " + (orderCount != null ? orderCount : "0"));
            System.out.println("   Toplam Gelir: $"
                    + (revenue != null ? String.format("%.2f", Double.parseDouble(revenue)) : "0.00"));

            // Top products
            System.out.println("\n🔥 Popüler Ürünler:");
            Set<String> popularityKeys = redis.keys(REDIS_PREFIX + "analytics:popularity:*");
            Map<String, Integer> popularProducts = new HashMap<>();

            for (String key : popularityKeys) {
                String productId = key.replace(REDIS_PREFIX + "analytics:popularity:", "");
                int count = Integer.parseInt(redis.get(key));
                popularProducts.put(productId, count);
            }

            popularProducts.entrySet().stream()
                    .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                    .limit(5)
                    .forEach(entry -> {
                        System.out.println("   " + entry.getKey() + ": " + entry.getValue() + " sipariş");
                    });

            // Active sessions
            Set<String> sessionKeys = redis.keys(REDIS_PREFIX + "session:*");
            System.out.println("\n👥 Aktif Kullanıcılar: " + sessionKeys.size());

        } catch (Exception e) {
            System.err.println("❌ Dashboard metrics hatası: " + e.getMessage());
        }
    }

    /**
     * Sistemleri kapatır
     */
    public void shutdown() {
        System.out.println("\n=== Sistemler Kapatılıyor ===");

        isRunning = false;

        try {
            if (kafkaProducer != null) {
                kafkaProducer.close();
                System.out.println("✅ Kafka producer kapatıldı");
            }

            if (kafkaConsumer != null) {
                kafkaConsumer.close();
                System.out.println("✅ Kafka consumer kapatıldı");
            }

            if (rabbitChannel != null) {
                rabbitChannel.close();
                System.out.println("✅ RabbitMQ channel kapatıldı");
            }

            if (rabbitConnection != null) {
                rabbitConnection.close();
                System.out.println("✅ RabbitMQ connection kapatıldı");
            }

            if (redis != null) {
                redis.close();
                System.out.println("✅ Redis bağlantısı kapatıldı");
            }

            System.out.println("✅ Tüm sistemler başarıyla kapatıldı");

        } catch (Exception e) {
            System.err.println("❌ Shutdown hatası: " + e.getMessage());
        }
    }

    /**
     * Ana method - full stack integration demo
     */
    public static void main(String[] args) {
        FullStackIntegration integration = new FullStackIntegration();

        try {
            System.out.println("🚀 Full Stack Integration Demo Başlıyor...\n");

            // 1. Tüm sistemleri başlat
            integration.initializeAllSystems();

            // 2. E-ticaret senaryosunu simüle et
            integration.simulateECommerceScenario();

            // 3. Biraz bekle ki event'ler işlensin
            Thread.sleep(10000);

            // 4. Dashboard metrics'lerini göster
            integration.showDashboardMetrics();

            System.out.println("\n🎉 Full Stack Integration Demo Tamamlandı!");
            System.out.println("💡 Bu demo Kafka, RabbitMQ, Redis ve Elasticsearch'ün");
            System.out.println("   gerçek bir e-ticaret platformunda nasıl entegre edilebileceğini gösterdi!");

        } catch (Exception e) {
            System.err.println("❌ Demo çalıştırma hatası: " + e.getMessage());
            e.printStackTrace();
        } finally {
            integration.shutdown();
        }
    }
}