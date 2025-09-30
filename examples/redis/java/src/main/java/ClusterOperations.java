package main.java;

import redis.clients.jedis.JedisCluster;
import redis.clients.jedis.HostAndPort;
import redis.clients.jedis.JedisPoolConfig;
import redis.clients.jedis.JedisPubSub;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.time.LocalDateTime;

/**
 * Redis Cluster Operations - İleri Düzey Kümeleme İşlemleri
 * 
 * Bu örnek Redis kümeleme (clustering) özelliklerini kapsamlı olarak gösterir:
 * - Cluster bağlantı yönetimi
 * - Yük dağıtımı ve failover
 * - Master-Slave yapılandırması
 * - Performans optimizasyonu
 * - İzleme ve sağlık kontrolleri
 * 
 * @author: Senior Software Architect
 * @version: 1.0
 */
public class ClusterOperations {

    private JedisCluster jedisCluster;
    private static final String CLUSTER_PREFIX = "app:cluster:";

    /**
     * Redis cluster bağlantısını başlatır
     * Üretim ortamında en az 3 master node kullanılmalıdır
     */
    public void initializeCluster() {
        System.out.println("=== Redis Cluster Bağlantısı Başlatılıyor ===");

        // Cluster node'larını tanımla
        Set<HostAndPort> clusterNodes = new HashSet<>();
        clusterNodes.add(new HostAndPort("localhost", 7000));
        clusterNodes.add(new HostAndPort("localhost", 7001));
        clusterNodes.add(new HostAndPort("localhost", 7002));
        clusterNodes.add(new HostAndPort("localhost", 7003));
        clusterNodes.add(new HostAndPort("localhost", 7004));
        clusterNodes.add(new HostAndPort("localhost", 7005));

        // Connection pool yapılandırması
        JedisPoolConfig poolConfig = new JedisPoolConfig();
        poolConfig.setMaxTotal(20); // Maksimum bağlantı sayısı
        poolConfig.setMaxIdle(10); // Maksimum boşta bekleyen bağlantı
        poolConfig.setMinIdle(5); // Minimum boşta bekleyen bağlantı
        poolConfig.setTestOnBorrow(true); // Bağlantı alırken test et
        poolConfig.setTestOnReturn(true); // Bağlantı geri verirken test et
        poolConfig.setTestWhileIdle(true); // Boşta beklerken test et
        poolConfig.setBlockWhenExhausted(true); // Pool dolduğunda bekle
        poolConfig.setMaxWaitMillis(5000); // Maksimum bekleme süresi

        try {
            // Cluster bağlantısını oluştur
            jedisCluster = new JedisCluster(clusterNodes, 5000, 5000, 3, poolConfig);
            System.out.println("✅ Redis Cluster bağlantısı başarılı!");

        } catch (Exception e) {
            System.err.println("❌ Cluster bağlantı hatası: " + e.getMessage());
            // Fallback: Tek node bağlantısı
            initializeFallbackConnection();
        }
    }

    /**
     * Cluster bağlantısı başarısız olursa tek node'a bağlan
     */
    private void initializeFallbackConnection() {
        System.out.println("⚠️ Fallback: Tek Redis node'una bağlanılıyor...");

        Set<HostAndPort> fallbackNodes = new HashSet<>();
        fallbackNodes.add(new HostAndPort("localhost", 6379));

        try {
            jedisCluster = new JedisCluster(fallbackNodes);
            System.out.println("✅ Fallback bağlantı başarılı!");
        } catch (Exception e) {
            System.err.println("❌ Fallback bağlantı da başarısız: " + e.getMessage());
        }
    }

    /**
     * Cluster durumunu kontrol eder
     */
    public void checkClusterHealth() {
        System.out.println("\n=== Cluster Sağlık Kontrolü ===");

        try {
            // Cluster bilgilerini al
            Map<String, Object> clusterInfo = new HashMap<>();

            // Test verileri ile cluster performansını kontrol et
            String testKey = CLUSTER_PREFIX + "health:test";
            String testValue = "cluster-test-" + System.currentTimeMillis();

            long startTime = System.currentTimeMillis();
            jedisCluster.set(testKey, testValue);
            String result = jedisCluster.get(testKey);
            long responseTime = System.currentTimeMillis() - startTime;

            clusterInfo.put("response_time_ms", responseTime);
            clusterInfo.put("read_write_test", result.equals(testValue) ? "PASS" : "FAIL");
            clusterInfo.put("timestamp", LocalDateTime.now());

            // Cluster node sayısını kontrol et (yaklaşık)
            try {
                jedisCluster.set(CLUSTER_PREFIX + "node:1", "test1");
                jedisCluster.set(CLUSTER_PREFIX + "node:2", "test2");
                jedisCluster.set(CLUSTER_PREFIX + "node:3", "test3");
                clusterInfo.put("multi_node_test", "PASS");
            } catch (Exception e) {
                clusterInfo.put("multi_node_test", "FAIL: " + e.getMessage());
            }

            // Sonuçları yazdır
            System.out.println("📊 Cluster Sağlık Raporu:");
            clusterInfo.forEach((key, value) -> System.out.println("   " + key + ": " + value));

            // Temizlik
            jedisCluster.del(testKey);
            jedisCluster.del(CLUSTER_PREFIX + "node:1");
            jedisCluster.del(CLUSTER_PREFIX + "node:2");
            jedisCluster.del(CLUSTER_PREFIX + "node:3");

        } catch (Exception e) {
            System.err.println("❌ Cluster sağlık kontrolü hatası: " + e.getMessage());
        }
    }

    /**
     * Cluster'da veri dağıtımını test eder
     */
    public void testDataDistribution() {
        System.out.println("\n=== Veri Dağıtım Testi ===");

        try {
            Map<String, String> distributionTest = new HashMap<>();

            // Farklı hash slot'lara düşecek anahtarlar oluştur
            for (int i = 0; i < 100; i++) {
                String key = CLUSTER_PREFIX + "dist:user:" + i;
                String value = "user_data_" + i + "_" + LocalDateTime.now();

                long startTime = System.nanoTime();
                jedisCluster.set(key, value);
                long endTime = System.nanoTime();

                distributionTest.put(key, value);

                if (i % 25 == 0) {
                    double latencyMs = (endTime - startTime) / 1_000_000.0;
                    System.out.printf("   📝 Anahtar %d: %.2f ms\n", i, latencyMs);
                }
            }

            System.out.println("✅ " + distributionTest.size() + " anahtar cluster'a dağıtıldı");

            // Okuma performansını test et
            System.out.println("\n📖 Okuma Performans Testi:");
            long totalReadTime = 0;
            int readCount = 0;

            for (String key : distributionTest.keySet()) {
                long startTime = System.nanoTime();
                String value = jedisCluster.get(key);
                long endTime = System.nanoTime();

                totalReadTime += (endTime - startTime);
                readCount++;

                if (value == null) {
                    System.err.println("⚠️ Anahtar bulunamadı: " + key);
                }
            }

            double avgReadLatency = (totalReadTime / readCount) / 1_000_000.0;
            System.out.printf("   📊 Ortalama okuma gecikmesi: %.2f ms\n", avgReadLatency);

            // Temizlik
            for (String key : distributionTest.keySet()) {
                jedisCluster.del(key);
            }

        } catch (Exception e) {
            System.err.println("❌ Veri dağıtım testi hatası: " + e.getMessage());
        }
    }

    /**
     * Cluster failover senaryosunu simüle eder
     */
    public void simulateFailoverScenario() {
        System.out.println("\n=== Failover Senaryo Simülasyonu ===");

        try {
            String failoverKey = CLUSTER_PREFIX + "failover:test";
            String originalValue = "failover_test_" + System.currentTimeMillis();

            // Orijinal veriyi yazıp kontrol et
            jedisCluster.set(failoverKey, originalValue);
            System.out.println("📝 Orijinal veri yazıldı: " + originalValue);

            // Sürekli okuma/yazma işlemlerini başlat
            CompletableFuture<Void> continuousOperations = CompletableFuture.runAsync(() -> {
                for (int i = 0; i < 50; i++) {
                    try {
                        // Veriyi güncelle
                        String newValue = originalValue + "_update_" + i;
                        jedisCluster.set(failoverKey, newValue);

                        // Veriyi oku
                        String readValue = jedisCluster.get(failoverKey);

                        if (readValue != null && readValue.equals(newValue)) {
                            System.out.println("✅ İşlem " + i + ": Başarılı");
                        } else {
                            System.out.println("⚠️ İşlem " + i + ": Veri tutarsızlığı");
                        }

                        Thread.sleep(100); // 100ms bekle

                    } catch (Exception e) {
                        System.out.println("❌ İşlem " + i + " hatası: " + e.getMessage());
                        // Hata durumunda retry logic
                        try {
                            Thread.sleep(500); // 500ms bekle ve tekrar dene
                        } catch (InterruptedException ie) {
                            Thread.currentThread().interrupt();
                            break;
                        }
                    }
                }
            });

            // Simülasyon tamamlanana kadar bekle
            try {
                continuousOperations.get(30, TimeUnit.SECONDS);
                System.out.println("✅ Failover simülasyonu tamamlandı");
            } catch (Exception e) {
                System.out.println("⏰ Failover simülasyonu timeout");
            }

            // Temizlik
            jedisCluster.del(failoverKey);

        } catch (Exception e) {
            System.err.println("❌ Failover simülasyonu hatası: " + e.getMessage());
        }
    }

    /**
     * Cluster performans metriklerini toplar
     */
    public void collectPerformanceMetrics() {
        System.out.println("\n=== Cluster Performans Metrikleri ===");

        try {
            Map<String, Object> metrics = new HashMap<>();

            // Yazma performansı testi
            long writeStartTime = System.currentTimeMillis();
            for (int i = 0; i < 1000; i++) {
                String key = CLUSTER_PREFIX + "perf:write:" + i;
                String value = "performance_test_data_" + i;
                jedisCluster.set(key, value);
            }
            long writeEndTime = System.currentTimeMillis();
            long writeDuration = writeEndTime - writeStartTime;

            metrics.put("write_operations", 1000);
            metrics.put("write_duration_ms", writeDuration);
            metrics.put("writes_per_second", 1000.0 / (writeDuration / 1000.0));

            // Okuma performansı testi
            long readStartTime = System.currentTimeMillis();
            for (int i = 0; i < 1000; i++) {
                String key = CLUSTER_PREFIX + "perf:write:" + i;
                jedisCluster.get(key);
            }
            long readEndTime = System.currentTimeMillis();
            long readDuration = readEndTime - readStartTime;

            metrics.put("read_operations", 1000);
            metrics.put("read_duration_ms", readDuration);
            metrics.put("reads_per_second", 1000.0 / (readDuration / 1000.0));

            // Batch işlem performansı
            Map<String, String> batchData = new HashMap<>();
            for (int i = 0; i < 100; i++) {
                batchData.put(CLUSTER_PREFIX + "perf:batch:" + i, "batch_value_" + i);
            }

            long batchStartTime = System.currentTimeMillis();
            // Note: JedisCluster mset desteklemiyor, tek tek set kullanıyoruz
            for (Map.Entry<String, String> entry : batchData.entrySet()) {
                jedisCluster.set(entry.getKey(), entry.getValue());
            }
            long batchEndTime = System.currentTimeMillis();

            metrics.put("batch_operations", batchData.size());
            metrics.put("batch_duration_ms", batchEndTime - batchStartTime);

            // Sonuçları yazdır
            System.out.println("📊 Performans Metrikleri:");
            metrics.forEach((key, value) -> {
                if (value instanceof Double) {
                    System.out.printf("   %s: %.2f\n", key, (Double) value);
                } else {
                    System.out.println("   " + key + ": " + value);
                }
            });

            // Temizlik
            for (int i = 0; i < 1000; i++) {
                jedisCluster.del(CLUSTER_PREFIX + "perf:write:" + i);
            }
            for (String key : batchData.keySet()) {
                jedisCluster.del(key);
            }

        } catch (Exception e) {
            System.err.println("❌ Performans metrikleri toplama hatası: " + e.getMessage());
        }
    }

    /**
     * Cluster monitoring dashboard simülasyonu
     */
    public void runMonitoringDashboard() {
        System.out.println("\n=== Cluster Monitoring Dashboard ===");

        try {
            // Real-time monitoring simulation
            for (int i = 0; i < 10; i++) {
                System.out.println("\n📊 Monitoring Döngüsü " + (i + 1) + "/10");

                // Anlık performans metrikleri
                long startTime = System.nanoTime();
                String testKey = CLUSTER_PREFIX + "monitor:test:" + i;
                jedisCluster.set(testKey, "monitoring_" + System.currentTimeMillis());
                String value = jedisCluster.get(testKey);
                long endTime = System.nanoTime();

                double latency = (endTime - startTime) / 1_000_000.0;

                // Dashboard göstergeleri
                System.out.printf("   🔄 Gecikme: %.2f ms\n", latency);
                System.out.printf("   📈 Durum: %s\n", value != null ? "ONLINE" : "OFFLINE");
                System.out.printf("   ⏰ Zaman: %s\n", LocalDateTime.now());

                // Memory usage simulation
                Runtime runtime = Runtime.getRuntime();
                long usedMemory = runtime.totalMemory() - runtime.freeMemory();
                System.out.printf("   💾 JVM Bellek: %.2f MB\n", usedMemory / 1024.0 / 1024.0);

                jedisCluster.del(testKey);

                // 2 saniye bekle
                Thread.sleep(2000);
            }

            System.out.println("\n✅ Monitoring dashboard simülasyonu tamamlandı");

        } catch (Exception e) {
            System.err.println("❌ Monitoring dashboard hatası: " + e.getMessage());
        }
    }

    /**
     * Cluster bağlantısını kapatır
     */
    public void close() {
        if (jedisCluster != null) {
            try {
                jedisCluster.close();
                System.out.println("✅ Redis Cluster bağlantısı kapatıldı");
            } catch (Exception e) {
                System.err.println("❌ Bağlantı kapatma hatası: " + e.getMessage());
            }
        }
    }

    /**
     * Ana method - tüm cluster işlemlerini çalıştırır
     */
    public static void main(String[] args) {
        ClusterOperations clusterOps = new ClusterOperations();

        try {
            System.out.println("🚀 Redis Cluster Operations Demo Başlıyor...\n");

            // 1. Cluster bağlantısını başlat
            clusterOps.initializeCluster();

            // 2. Cluster sağlığını kontrol et
            clusterOps.checkClusterHealth();

            // 3. Veri dağıtımını test et
            clusterOps.testDataDistribution();

            // 4. Failover senaryosunu simüle et
            clusterOps.simulateFailoverScenario();

            // 5. Performans metriklerini topla
            clusterOps.collectPerformanceMetrics();

            // 6. Monitoring dashboard'u çalıştır
            clusterOps.runMonitoringDashboard();

            System.out.println("\n🎉 Redis Cluster Operations Demo Tamamlandı!");

        } catch (Exception e) {
            System.err.println("❌ Demo çalıştırma hatası: " + e.getMessage());
            e.printStackTrace();
        } finally {
            clusterOps.close();
        }
    }
}