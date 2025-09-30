package com.example.kafka;

import org.apache.kafka.clients.producer.*;
import java.util.Properties;
import java.util.concurrent.Future;

/**
 * Kafka Producer örneği - Mesaj gönderme işlemleri
 * 
 * Bu sınıf farklı producer pattern'lerini gösterir:
 * - Senkron mesaj gönderme (blocking)
 * - Asenkron mesaj gönderme (non-blocking) 
 * - Belirli partition'a gönderme
 * - Error handling ve retry mekanizmaları
 */
public class SimpleProducer {
    
    private final Producer<String, String> producer;
    private final String topicName;
    
    /**
     * Producer yapılandırması ve initialization
     */
    public SimpleProducer(String topicName) {
        this.topicName = topicName;
        
        // Producer yapılandırması
        Properties props = new Properties();
        
        // Bootstrap servers - Kafka cluster bağlantı noktası
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        
        // Serializer'lar - Key ve value için string serialization
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, 
                  "org.apache.kafka.common.serialization.StringSerializer");
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, 
                  "org.apache.kafka.common.serialization.StringSerializer");
        
        // Delivery guarantee ayarları
        props.put(ProducerConfig.ACKS_CONFIG, "all");  // Tüm replica'lardan ack bekle
        props.put(ProducerConfig.RETRIES_CONFIG, 3);   // 3 kez retry yap
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);  // Duplicate prevention
        
        // Performance tuning
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, 16384);      // 16KB batch size
        props.put(ProducerConfig.LINGER_MS_CONFIG, 10);          // 10ms batch bekleme
        props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, 33554432); // 32MB buffer
        props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "gzip"); // GZIP compression
        
        this.producer = new KafkaProducer<>(props);
    }
    
    /**
     * Senkron mesaj gönderme - Blocking operation
     * 
     * Avantajları:
     * - Immediate feedback (başarı/başarısızlık)
     * - Simple error handling
     * 
     * Dezavantajları:
     * - Lower throughput (blocking operation)
     * - Higher latency
     */
    public void sendMessageSync(String key, String value) {
        try {
            ProducerRecord<String, String> record = 
                new ProducerRecord<>(topicName, key, value);
            
            // Send işlemi ve metadata'yı bekleme
            RecordMetadata metadata = producer.send(record).get();
            
            System.out.printf("✅ Message sent successfully: " +
                "Topic=%s, Partition=%d, Offset=%d, Timestamp=%d%n",
                metadata.topic(), metadata.partition(), 
                metadata.offset(), metadata.timestamp());
                
        } catch (Exception e) {
            System.err.println("❌ Error sending message: " + e.getMessage());
        }
    }
    
    /**
     * Asenkron mesaj gönderme - Non-blocking operation
     * 
     * Avantajları:
     * - Higher throughput (non-blocking)
     * - Lower latency
     * - Better resource utilization
     * 
     * Dezavantajları:
     * - Complex error handling
     * - Callback management
     */
    public void sendMessageAsync(String key, String value) {
        ProducerRecord<String, String> record = 
            new ProducerRecord<>(topicName, key, value);
        
        // Callback ile asenkron handling
        producer.send(record, new Callback() {
            @Override
            public void onCompletion(RecordMetadata metadata, Exception exception) {
                if (exception != null) {
                    System.err.println("❌ Failed to send message: " + exception.getMessage());
                } else {
                    System.out.printf("✅ Message sent async: Topic=%s, Partition=%d, Offset=%d%n",
                        metadata.topic(), metadata.partition(), metadata.offset());
                }
            }
        });
    }
    
    /**
     * Partition belirterek mesaj gönderme
     * 
     * Kullanım senaryoları:
     * - Specific partition'a routing
     * - Load balancing control
     * - Ordered processing guarantee
     */
    public void sendToSpecificPartition(String key, String value, int partition) {
        ProducerRecord<String, String> record = 
            new ProducerRecord<>(topicName, partition, key, value);
        
        producer.send(record, (metadata, exception) -> {
            if (exception != null) {
                System.err.println("❌ Send failed: " + exception.getMessage());
            } else {
                System.out.printf("✅ Sent to partition %d with offset %d%n",
                    metadata.partition(), metadata.offset());
            }
        });
    }
    
    /**
     * Batch mesaj gönderme - Performance optimized
     * 
     * Birden fazla mesajı batch halinde gönderir
     */
    public void sendMessageBatch(String[] keys, String[] values) {
        if (keys.length != values.length) {
            throw new IllegalArgumentException("Keys and values arrays must have same length");
        }
        
        for (int i = 0; i < keys.length; i++) {
            // Asenkron send - batch'lenecek
            sendMessageAsync(keys[i], values[i]);
        }
        
        // Tüm mesajların gönderilmesini bekle
        producer.flush();
        System.out.println("✅ Batch of " + keys.length + " messages sent successfully");
    }
    
    /**
     * Producer'ı güvenli şekilde kapatma
     * 
     * Pending mesajların gönderilmesini bekler ve resources'ları temizler
     */
    public void close() {
        try {
            // Pending mesajları gönder
            producer.flush();
            
            // Producer'ı kapat
            producer.close();
            
            System.out.println("✅ Producer closed successfully");
        } catch (Exception e) {
            System.err.println("❌ Error closing producer: " + e.getMessage());
        }
    }
    
    /**
     * Producer metrics ve performance bilgileri
     */
    public void printMetrics() {
        producer.metrics().forEach((metricName, metric) -> {
            if (metricName.name().contains("record-send-rate") || 
                metricName.name().contains("batch-size-avg")) {
                System.out.printf("📊 %s: %.2f%n", metricName.name(), metric.metricValue());
            }
        });
    }
    
    /**
     * Test main method - Farklı send pattern'lerini demonstrasyonu
     */
    public static void main(String[] args) {
        SimpleProducer producer = new SimpleProducer("user-events");
        
        try {
            System.out.println("🚀 Starting Kafka Producer demo...");
            
            // 1. Senkron mesaj gönderme test
            System.out.println("\n📤 Testing synchronous send:");
            for (int i = 0; i < 3; i++) {
                String key = "sync-user-" + i;
                String value = "Synchronous message " + i + " at " + System.currentTimeMillis();
                producer.sendMessageSync(key, value);
                Thread.sleep(500); // 500ms bekleme
            }
            
            // 2. Asenkron mesaj gönderme test
            System.out.println("\n📤 Testing asynchronous send:");
            for (int i = 0; i < 5; i++) {
                String key = "async-user-" + i;
                String value = "Asynchronous message " + i + " at " + System.currentTimeMillis();
                producer.sendMessageAsync(key, value);
            }
            
            // Asenkron mesajların gönderilmesini bekle
            Thread.sleep(2000);
            
            // 3. Specific partition test
            System.out.println("\n📤 Testing specific partition send:");
            producer.sendToSpecificPartition("partition-test", "Message to partition 0", 0);
            
            // 4. Batch send test
            System.out.println("\n📤 Testing batch send:");
            String[] keys = {"batch-1", "batch-2", "batch-3", "batch-4", "batch-5"};
            String[] values = {
                "Batch message 1", "Batch message 2", "Batch message 3",
                "Batch message 4", "Batch message 5"
            };
            producer.sendMessageBatch(keys, values);
            
            // 5. Metrics gösterimi
            System.out.println("\n📊 Producer Metrics:");
            producer.printMetrics();
            
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.err.println("❌ Producer interrupted");
        } catch (Exception e) {
            System.err.println("❌ Producer error: " + e.getMessage());
        } finally {
            producer.close();
        }
    }
}