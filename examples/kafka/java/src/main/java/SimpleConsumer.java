package com.example.kafka;

import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.TopicPartition;
import java.time.Duration;
import java.util.*;

/**
 * Kafka Consumer örneği - Mesaj tüketme işlemleri
 * 
 * Bu sınıf farklı consumer pattern'lerini gösterir:
 * - Otomatik commit ile tüketme
 * - Manuel commit ile tüketme (daha güvenli)
 * - Batch commit ile tüketme (performance optimized)
 * - Belirli partition'dan tüketme
 * - Error handling ve recovery
 */
public class SimpleConsumer {
    
    private final Consumer<String, String> consumer;
    private final String topicName;
    
    /**
     * Consumer yapılandırması ve initialization
     */
    public SimpleConsumer(String groupId, String topicName) {
        this.topicName = topicName;
        
        // Consumer yapılandırması
        Properties props = new Properties();
        
        // Bootstrap servers - Kafka cluster bağlantı noktası
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        
        // Consumer group yapılandırması
        props.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
        props.put(ConsumerConfig.GROUP_INSTANCE_ID_CONFIG, "consumer-" + System.currentTimeMillis());
        
        // Deserializer'lar - Key ve value için string deserialization
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, 
                  "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, 
                  "org.apache.kafka.common.serialization.StringDeserializer");
        
        // Offset management
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest"); // earliest, latest, none
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);     // Manuel commit control
        
        // Session management - Consumer group membership
        props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, 30000);     // 30 saniye
        props.put(ConsumerConfig.HEARTBEAT_INTERVAL_MS_CONFIG, 3000);   // 3 saniye
        props.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, 300000);  // 5 dakika
        
        // Fetch configuration - Performance tuning
        props.put(ConsumerConfig.FETCH_MIN_BYTES_CONFIG, 1024);         // Minimum fetch size
        props.put(ConsumerConfig.FETCH_MAX_WAIT_MS_CONFIG, 500);        // Maximum wait time
        props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 100);         // Records per poll
        
        this.consumer = new KafkaConsumer<>(props);
    }
    
    /**
     * Otomatik commit ile mesaj tüketme
     * 
     * Avantajları:
     * - Simple implementation
     * - Automatic offset management
     * 
     * Dezavantajları:
     * - Risk of message loss
     * - No control over commit timing
     * - Possible duplicate processing
     */
    public void consumeWithAutoCommit() {
        // Auto commit'i enable et (test için)
        Properties props = new Properties();
        props.putAll(consumer.getConfig());
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, true);
        props.put(ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, 5000); // 5 saniye
        
        Consumer<String, String> autoCommitConsumer = new KafkaConsumer<>(props);
        autoCommitConsumer.subscribe(Arrays.asList(topicName));
        
        try {
            System.out.println("🔄 Starting auto-commit consumer...");
            
            while (true) {
                // Polling - Broker'dan mesaj çekme
                ConsumerRecords<String, String> records = 
                    autoCommitConsumer.poll(Duration.ofMillis(1000));
                
                // Her record'u işleme
                for (ConsumerRecord<String, String> record : records) {
                    processMessage(record);
                }
                
                // Auto commit enabled ise otomatik commit olur
                System.out.printf("📊 Processed %d messages (auto-commit)%n", records.count());
            }
        } catch (Exception e) {
            System.err.println("❌ Error in auto-commit consumer: " + e.getMessage());
        } finally {
            autoCommitConsumer.close();
        }
    }
    
    /**
     * Manuel commit ile mesaj tüketme - Daha güvenli
     * 
     * Avantajları:
     * - Full control over offset management
     * - No message loss risk
     * - Transactional processing
     * 
     * Dezavantajları:
     * - More complex implementation
     * - Manual error handling required
     * - Possible duplicate processing on failure
     */
    public void consumeWithManualCommit() {
        consumer.subscribe(Arrays.asList(topicName));
        
        try {
            System.out.println("🔄 Starting manual-commit consumer...");
            
            while (true) {
                ConsumerRecords<String, String> records = 
                    consumer.poll(Duration.ofMillis(1000));
                
                for (ConsumerRecord<String, String> record : records) {
                    try {
                        // Mesajı işle
                        processMessage(record);
                        
                        // Başarılı işlem sonrası manuel commit
                        Map<TopicPartition, OffsetAndMetadata> offsets = new HashMap<>();
                        offsets.put(
                            new TopicPartition(record.topic(), record.partition()),
                            new OffsetAndMetadata(record.offset() + 1)
                        );
                        consumer.commitSync(offsets);
                        
                        System.out.printf("✅ Committed offset %d for partition %d%n", 
                            record.offset() + 1, record.partition());
                        
                    } catch (Exception e) {
                        System.err.printf("❌ Error processing message at offset %d: %s%n", 
                            record.offset(), e.getMessage());
                        // Hata durumunda commit yapılmaz, mesaj tekrar işlenir
                        break; // Bu batch'i durdur
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("❌ Error in manual-commit consumer: " + e.getMessage());
        } finally {
            consumer.close();
        }
    }
    
    /**
     * Batch commit ile mesaj tüketme - Performance optimized
     * 
     * Avantajları:
     * - Higher throughput
     * - Reduced commit overhead
     * - Better performance
     * 
     * Dezavantajları:
     * - Risk of reprocessing batch on failure
     * - Less granular error handling
     */
    public void consumeWithBatchCommit() {
        consumer.subscribe(Arrays.asList(topicName));
        
        try {
            System.out.println("🔄 Starting batch-commit consumer...");
            
            while (true) {
                ConsumerRecords<String, String> records = 
                    consumer.poll(Duration.ofMillis(1000));
                
                if (records.isEmpty()) {
                    continue;
                }
                
                boolean allProcessedSuccessfully = true;
                int processedCount = 0;
                
                // Tüm mesajları işle
                for (ConsumerRecord<String, String> record : records) {
                    try {
                        processMessage(record);
                        processedCount++;
                    } catch (Exception e) {
                        System.err.printf("❌ Error processing message at offset %d: %s%n", 
                            record.offset(), e.getMessage());
                        allProcessedSuccessfully = false;
                        break; // Hata durumunda batch'i durdur
                    }
                }
                
                // Tüm mesajlar başarılı ise batch commit
                if (allProcessedSuccessfully && processedCount > 0) {
                    try {
                        consumer.commitSync(); // Tüm partition'lar için commit
                        System.out.printf("✅ Batch committed successfully: %d records%n", processedCount);
                    } catch (CommitFailedException e) {
                        System.err.println("❌ Commit failed: " + e.getMessage());
                    }
                } else {
                    System.out.printf("⚠️ Batch processing failed, skipping commit. Processed: %d/%d%n", 
                        processedCount, records.count());
                }
            }
        } catch (Exception e) {
            System.err.println("❌ Error in batch-commit consumer: " + e.getMessage());
        } finally {
            consumer.close();
        }
    }
    
    /**
     * Belirli partition'dan mesaj tüketme
     * 
     * Kullanım senaryoları:
     * - Specific partition monitoring
     * - Manual partition assignment
     * - Testing ve debugging
     */
    public void consumeFromSpecificPartition(int partition) {
        TopicPartition topicPartition = new TopicPartition(topicName, partition);
        consumer.assign(Arrays.asList(topicPartition));
        
        // Belirli offset'ten başlatma (opsiyonel)
        consumer.seekToBeginning(Arrays.asList(topicPartition));
        
        try {
            System.out.printf("🔄 Starting consumer for partition %d...%n", partition);
            
            while (true) {
                ConsumerRecords<String, String> records = 
                    consumer.poll(Duration.ofMillis(1000));
                
                for (ConsumerRecord<String, String> record : records) {
                    System.out.printf("📨 Partition %d, Offset %d: %s = %s%n",
                        record.partition(), record.offset(), record.key(), record.value());
                }
                
                if (!records.isEmpty()) {
                    consumer.commitSync();
                }
            }
        } catch (Exception e) {
            System.err.println("❌ Error in partition consumer: " + e.getMessage());
        } finally {
            consumer.close();
        }
    }
    
    /**
     * Consumer lag monitoring - Performance monitoring
     */
    public void monitorConsumerLag() {
        consumer.subscribe(Arrays.asList(topicName));
        
        try {
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                
                // Consumer lag hesaplama
                for (TopicPartition partition : consumer.assignment()) {
                    long currentOffset = consumer.position(partition);
                    
                    Map<TopicPartition, Long> endOffsets = consumer.endOffsets(
                        Collections.singletonList(partition));
                    long endOffset = endOffsets.get(partition);
                    
                    long lag = endOffset - currentOffset;
                    
                    if (lag > 0) {
                        System.out.printf("⚠️ Consumer lag: Partition %d, Current: %d, End: %d, Lag: %d%n",
                            partition.partition(), currentOffset, endOffset, lag);
                    }
                }
                
                // Mesajları işle
                for (ConsumerRecord<String, String> record : records) {
                    processMessage(record);
                }
                
                if (!records.isEmpty()) {
                    consumer.commitSync();
                }
                
                Thread.sleep(5000); // 5 saniye lag monitoring
            }
        } catch (Exception e) {
            System.err.println("❌ Error in lag monitoring: " + e.getMessage());
        } finally {
            consumer.close();
        }
    }
    
    /**
     * Mesaj işleme business logic'i
     * 
     * Bu method'da gerçek business logic implementasyonu yapılır
     */
    private void processMessage(ConsumerRecord<String, String> record) {
        // Business logic implementation
        System.out.printf("🔄 Processing message: Key=%s, Value=%s, " +
            "Partition=%d, Offset=%d, Timestamp=%d%n",
            record.key(), record.value(), record.partition(), 
            record.offset(), record.timestamp());
        
        // Simulate processing time
        try {
            Thread.sleep(100); // 100ms işlem süresi simülasyonu
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Processing interrupted", e);
        }
        
        // Simulated business logic validation
        if (record.value() != null && record.value().contains("error")) {
            throw new RuntimeException("Simulated processing error");
        }
    }
    
    /**
     * Consumer metrics ve performance bilgileri
     */
    public void printMetrics() {
        consumer.metrics().forEach((metricName, metric) -> {
            if (metricName.name().contains("records-consumed-rate") || 
                metricName.name().contains("records-lag-max")) {
                System.out.printf("📊 %s: %.2f%n", metricName.name(), metric.metricValue());
            }
        });
    }
    
    /**
     * Test main method - Farklı consumer pattern'lerini demonstrasyonu
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java SimpleConsumer <mode>");
            System.out.println("Modes: auto, manual, batch, partition, lag");
            return;
        }
        
        String mode = args[0];
        SimpleConsumer consumer = new SimpleConsumer("test-consumer-group", "user-events");
        
        try {
            System.out.println("🚀 Starting Kafka Consumer demo in " + mode + " mode...");
            
            switch (mode.toLowerCase()) {
                case "auto":
                    consumer.consumeWithAutoCommit();
                    break;
                case "manual":
                    consumer.consumeWithManualCommit();
                    break;
                case "batch":
                    consumer.consumeWithBatchCommit();
                    break;
                case "partition":
                    consumer.consumeFromSpecificPartition(0);
                    break;
                case "lag":
                    consumer.monitorConsumerLag();
                    break;
                default:
                    System.out.println("❌ Unknown mode: " + mode);
                    break;
            }
            
        } catch (Exception e) {
            System.err.println("❌ Consumer error: " + e.getMessage());
        }
    }
}