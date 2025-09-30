# Redis Clustering ve Production Deployment

## 📋 Özet

Bu bölümde Redis'in horizontal scaling çözümü olan Redis Cluster'ı öğreneceksiniz. High availability, automatic failover, data sharding ve production deployment stratejilerini kapsamlı olarak ele alacağız.

## 🎯 Learning Objectives

Bu bölümü tamamladığında:

- ✅ Redis Cluster architecture'ını anlayabileceksin
- ✅ Multi-node Redis cluster kurabileceksin
- ✅ Data sharding ve hash slots kavramlarını uygulayabileceksin
- ✅ Automatic failover ve high availability sağlayabileceksin
- ✅ Cluster management operations yapabileceksin
- ✅ Production deployment strategies uygulayabileceksin
- ✅ Performance monitoring ve optimization yapabileceksin

## 📋 Prerequisites

- Redis basic operations ve data structures
- Redis Sentinel ve replication bilgisi
- Docker ve container orchestration
- Linux system administration
- Network ve cluster concepts

## 🏗️ Redis Cluster Architecture

### Cluster Topology

```
                    Redis Cluster (6 nodes minimum)

    Master 1 (0-5460)      Master 2 (5461-10922)     Master 3 (10923-16383)
         |                        |                         |
    Slave 1-1               Slave 2-1                 Slave 3-1

    Hash Slots: 16384 total
    Data Distribution: Automatic sharding based on key hash
    Replication: Each master has at least one slave
    Failover: Automatic when master fails
```

### Key Concepts

1. **Hash Slots**: 16384 slots, her key bir slot'a map edilir
2. **Sharding**: Data otomatik olarak master node'lara dağıtılır
3. **Replication**: Her master'ın en az bir slave'i vardır
4. **Failover**: Master fail olursa slave otomatik promote edilir
5. **Gossip Protocol**: Node'lar arası iletişim için kullanılır

## 🐳 Docker ile Redis Cluster

### Docker Compose Configuration

```yaml
# deployment/docker-compose/redis-cluster.yml
version: "3.8"

services:
  redis-cluster:
    image: redis:7.2-alpine
    container_name: redis-cluster-setup
    depends_on:
      - redis-1
      - redis-2
      - redis-3
      - redis-4
      - redis-5
      - redis-6
    networks:
      - redis-network
    command: >
      sh -c "
        sleep 10 &&
        redis-cli --cluster create
        redis-1:6379 redis-2:6379 redis-3:6379
        redis-4:6379 redis-5:6379 redis-6:6379
        --cluster-replicas 1 --cluster-yes
      "

  # Master Nodes
  redis-1:
    image: redis:7.2-alpine
    container_name: redis-cluster-1
    ports:
      - "7001:6379"
      - "17001:16379"
    volumes:
      - redis-1-data:/data
      - ./config/redis-cluster.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - redis-network
    restart: unless-stopped

  redis-2:
    image: redis:7.2-alpine
    container_name: redis-cluster-2
    ports:
      - "7002:6379"
      - "17002:16379"
    volumes:
      - redis-2-data:/data
      - ./config/redis-cluster.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - redis-network
    restart: unless-stopped

  redis-3:
    image: redis:7.2-alpine
    container_name: redis-cluster-3
    ports:
      - "7003:6379"
      - "17003:16379"
    volumes:
      - redis-3-data:/data
      - ./config/redis-cluster.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - redis-network
    restart: unless-stopped

  # Slave Nodes
  redis-4:
    image: redis:7.2-alpine
    container_name: redis-cluster-4
    ports:
      - "7004:6379"
      - "17004:16379"
    volumes:
      - redis-4-data:/data
      - ./config/redis-cluster.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - redis-network
    restart: unless-stopped

  redis-5:
    image: redis:7.2-alpine
    container_name: redis-cluster-5
    ports:
      - "7005:6379"
      - "17005:16379"
    volumes:
      - redis-5-data:/data
      - ./config/redis-cluster.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - redis-network
    restart: unless-stopped

  redis-6:
    image: redis:7.2-alpine
    container_name: redis-cluster-6
    ports:
      - "7006:6379"
      - "17006:16379"
    volumes:
      - redis-6-data:/data
      - ./config/redis-cluster.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - redis-network
    restart: unless-stopped

  # Redis Cluster Monitoring
  redis-insight:
    image: redislabs/redisinsight:latest
    container_name: redis-insight
    ports:
      - "8001:8001"
    networks:
      - redis-network
    restart: unless-stopped

volumes:
  redis-1-data:
  redis-2-data:
  redis-3-data:
  redis-4-data:
  redis-5-data:
  redis-6-data:

networks:
  redis-network:
    driver: bridge
```

### Redis Cluster Configuration

```conf
# config/redis-cluster.conf
# Basic Configuration
port 6379
bind 0.0.0.0
protected-mode no

# Cluster Configuration
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
cluster-announce-ip 127.0.0.1
cluster-announce-port 6379
cluster-announce-bus-port 16379

# Persistence
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000

# Memory Management
maxmemory 512mb
maxmemory-policy allkeys-lru

# Logging
loglevel notice
logfile /var/log/redis/redis.log

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Security (Production'da enable edilmeli)
# requirepass your_strong_password
# masterauth your_strong_password
```

## 💻 Python ile Redis Cluster Management

```python
# redis_cluster_manager.py
import redis
from rediscluster import RedisCluster
import time
import random
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading

class RedisClusterManager:
    """
    Redis Cluster Management ve Operations
    """

    def __init__(self, startup_nodes=None):
        """
        Redis Cluster client initialize
        """
        if startup_nodes is None:
            startup_nodes = [
                {"host": "localhost", "port": "7001"},
                {"host": "localhost", "port": "7002"},
                {"host": "localhost", "port": "7003"},
                {"host": "localhost", "port": "7004"},
                {"host": "localhost", "port": "7005"},
                {"host": "localhost", "port": "7006"}
            ]

        try:
            self.cluster = RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                skip_full_coverage_check=True,
                health_check_interval=30
            )
            print(f"✅ Redis Cluster connected - {len(startup_nodes)} nodes")
        except Exception as e:
            print(f"❌ Cluster connection failed: {e}")
            self.cluster = None

    def cluster_info(self) -> Dict:
        """
        Cluster bilgilerini al
        """
        if not self.cluster:
            return {}

        try:
            # Cluster nodes bilgisi
            nodes_info = self.cluster.cluster_nodes()

            # Cluster slots bilgisi
            slots_info = self.cluster.cluster_slots()

            # Her node için detaylı bilgi
            cluster_status = {
                'total_nodes': len(nodes_info),
                'masters': 0,
                'slaves': 0,
                'nodes': [],
                'slots_distribution': {}
            }

            for node_id, node_info in nodes_info.items():
                node_details = {
                    'id': node_id,
                    'ip_port': f"{node_info['ip']}:{node_info['port']}",
                    'role': 'master' if 'master' in node_info['flags'] else 'slave',
                    'status': 'connected' if 'connected' in node_info['flags'] else 'disconnected',
                    'slots': node_info.get('slots', [])
                }

                if node_details['role'] == 'master':
                    cluster_status['masters'] += 1
                    # Slots sayısını hesapla
                    slots_count = 0
                    for slot_range in node_info.get('slots', []):
                        if len(slot_range) == 2:
                            slots_count += slot_range[1] - slot_range[0] + 1
                    cluster_status['slots_distribution'][node_id] = slots_count
                else:
                    cluster_status['slaves'] += 1

                cluster_status['nodes'].append(node_details)

            return cluster_status

        except Exception as e:
            print(f"❌ Cluster info error: {e}")
            return {}

    def data_distribution_test(self, num_keys: int = 1000) -> Dict:
        """
        Data distribution test - keys nasıl dağıtılıyor
        """
        if not self.cluster:
            return {}

        print(f"📊 Testing data distribution with {num_keys} keys...")

        # Test data'sını yazalım
        key_distribution = {}

        for i in range(num_keys):
            key = f"test:key:{i}"
            value = f"value_{i}"

            try:
                # Key'i yaz
                self.cluster.set(key, value)

                # Bu key hangi node'da?
                node_info = self.cluster.cluster_keyslot(key)
                slot_number = self.cluster.cluster_keyslot(key)

                if slot_number not in key_distribution:
                    key_distribution[slot_number] = 0
                key_distribution[slot_number] += 1

            except Exception as e:
                print(f"❌ Error writing key {key}: {e}")

        # Sonuçları analiz et
        distribution_stats = {
            'total_keys': num_keys,
            'unique_slots_used': len(key_distribution),
            'min_keys_per_slot': min(key_distribution.values()) if key_distribution else 0,
            'max_keys_per_slot': max(key_distribution.values()) if key_distribution else 0,
            'avg_keys_per_slot': sum(key_distribution.values()) / len(key_distribution) if key_distribution else 0,
            'slot_distribution': key_distribution
        }

        print(f"   ✅ Distribution test completed")
        print(f"   📈 Keys distributed across {distribution_stats['unique_slots_used']} slots")
        print(f"   📊 Average keys per slot: {distribution_stats['avg_keys_per_slot']:.2f}")

        return distribution_stats

    def failover_simulation(self, node_to_fail: str = "7001") -> Dict:
        """
        Failover simulation - bir master node'u kapatıp ne olduğunu gözlemle
        """
        print(f"🔄 Simulating failover for node on port {node_to_fail}...")

        # Başlangıç durumu
        initial_status = self.cluster_info()
        print(f"   📊 Initial status: {initial_status['masters']} masters, {initial_status['slaves']} slaves")

        # Test data'sı yaz
        test_keys = {}
        for i in range(100):
            key = f"failover:test:{i}"
            value = f"test_value_{i}"
            test_keys[key] = value
            self.cluster.set(key, value)

        print(f"   📝 Written {len(test_keys)} test keys")

        # Node'u simüle olarak "fail" et (gerçekte kapatmayacağız)
        # Bunun yerine node durumunu kontrol edelim
        time.sleep(5)

        # Failover sonrası durum
        post_failover_status = self.cluster_info()

        # Test data'sının hala erişilebilir olduğunu kontrol et
        accessible_keys = 0
        for key in test_keys:
            try:
                value = self.cluster.get(key)
                if value == test_keys[key]:
                    accessible_keys += 1
            except Exception as e:
                print(f"   ❌ Key {key} not accessible: {e}")

        failover_results = {
            'initial_masters': initial_status['masters'],
            'initial_slaves': initial_status['slaves'],
            'post_failover_masters': post_failover_status['masters'],
            'post_failover_slaves': post_failover_status['slaves'],
            'test_keys_total': len(test_keys),
            'test_keys_accessible': accessible_keys,
            'data_availability_percentage': (accessible_keys / len(test_keys)) * 100
        }

        print(f"   ✅ Failover simulation completed")
        print(f"   📊 Data availability: {failover_results['data_availability_percentage']:.1f}%")

        return failover_results

    def performance_benchmark(self, num_operations: int = 10000) -> Dict:
        """
        Cluster performance benchmark
        """
        print(f"⚡ Running performance benchmark with {num_operations} operations...")

        benchmark_results = {
            'total_operations': num_operations,
            'write_operations': 0,
            'read_operations': 0,
            'failed_operations': 0,
            'start_time': time.time(),
            'end_time': None,
            'operations_per_second': 0
        }

        # Write benchmark
        write_start = time.time()
        for i in range(num_operations // 2):
            try:
                key = f"benchmark:write:{i}"
                value = f"benchmark_value_{i}_{random.randint(1000, 9999)}"
                self.cluster.set(key, value)
                benchmark_results['write_operations'] += 1
            except Exception as e:
                benchmark_results['failed_operations'] += 1

        write_end = time.time()
        write_duration = write_end - write_start

        # Read benchmark
        read_start = time.time()
        for i in range(num_operations // 2):
            try:
                key = f"benchmark:write:{i}"
                value = self.cluster.get(key)
                benchmark_results['read_operations'] += 1
            except Exception as e:
                benchmark_results['failed_operations'] += 1

        read_end = time.time()
        read_duration = read_end - read_start

        benchmark_results['end_time'] = time.time()
        total_duration = benchmark_results['end_time'] - benchmark_results['start_time']
        successful_ops = benchmark_results['write_operations'] + benchmark_results['read_operations']
        benchmark_results['operations_per_second'] = successful_ops / total_duration

        benchmark_results['write_ops_per_second'] = benchmark_results['write_operations'] / write_duration
        benchmark_results['read_ops_per_second'] = benchmark_results['read_operations'] / read_duration

        print(f"   ✅ Benchmark completed in {total_duration:.2f} seconds")
        print(f"   📊 Total OPS: {benchmark_results['operations_per_second']:.2f}")
        print(f"   ✍️  Write OPS: {benchmark_results['write_ops_per_second']:.2f}")
        print(f"   📖 Read OPS: {benchmark_results['read_ops_per_second']:.2f}")
        print(f"   ❌ Failed operations: {benchmark_results['failed_operations']}")

        return benchmark_results

    def cluster_scaling_demo(self):
        """
        Cluster scaling demonstration
        """
        print("📈 Cluster Scaling Demo")
        print("=" * 40)

        # Mevcut cluster durumu
        current_status = self.cluster_info()
        print(f"📊 Current cluster status:")
        print(f"   Masters: {current_status['masters']}")
        print(f"   Slaves: {current_status['slaves']}")
        print(f"   Total nodes: {current_status['total_nodes']}")

        # Slots distribution
        print(f"\n📋 Slots distribution:")
        for node_id, slot_count in current_status.get('slots_distribution', {}).items():
            print(f"   Node {node_id[:8]}...: {slot_count} slots")

        # Data distribution test
        print(f"\n📊 Data distribution analysis:")
        distribution = self.data_distribution_test(1000)

        # Performance test
        print(f"\n⚡ Performance analysis:")
        performance = self.performance_benchmark(5000)

        return {
            'cluster_status': current_status,
            'data_distribution': distribution,
            'performance': performance
        }

class RedisClusterApplication:
    """
    Redis Cluster ile gerçek dünya uygulaması
    """

    def __init__(self, cluster_manager: RedisClusterManager):
        self.cluster = cluster_manager.cluster
        self.manager = cluster_manager

    def distributed_cache_example(self):
        """
        Distributed cache example
        """
        print("🗃️  Distributed Cache Example")
        print("=" * 35)

        # Farklı data type'ları test et
        cache_operations = [
            # Simple key-value
            ("cache:user:1001", json.dumps({"id": 1001, "name": "Alice", "email": "alice@example.com"})),
            ("cache:user:1002", json.dumps({"id": 1002, "name": "Bob", "email": "bob@example.com"})),

            # Session data
            ("session:abc123", json.dumps({"user_id": 1001, "login_time": "2023-01-01T10:00:00", "permissions": ["read", "write"]})),
            ("session:xyz789", json.dumps({"user_id": 1002, "login_time": "2023-01-01T11:00:00", "permissions": ["read"]})),
        ]

        # Cache'e yaz
        for key, value in cache_operations:
            try:
                # TTL ile birlikte
                self.cluster.setex(key, 3600, value)  # 1 hour TTL
                print(f"   ✅ Cached: {key}")
            except Exception as e:
                print(f"   ❌ Cache error for {key}: {e}")

        # Cache'den oku
        print(f"\n📖 Reading from cache:")
        for key, _ in cache_operations:
            try:
                cached_value = self.cluster.get(key)
                if cached_value:
                    data = json.loads(cached_value)
                    print(f"   📄 {key}: {data}")
                else:
                    print(f"   ❌ Cache miss: {key}")
            except Exception as e:
                print(f"   ❌ Read error for {key}: {e}")

    def distributed_counter_example(self):
        """
        Distributed counter example - atomic operations
        """
        print("\n🔢 Distributed Counter Example")
        print("=" * 35)

        counters = ["page_views", "api_calls", "user_registrations"]

        # Parallel counter increments simulation
        def increment_counter(counter_name: str, count: int):
            for i in range(count):
                try:
                    current_value = self.cluster.incr(f"counter:{counter_name}")
                    if i % 100 == 0:  # Her 100'de bir log
                        print(f"   📊 {counter_name}: {current_value}")
                except Exception as e:
                    print(f"   ❌ Counter error: {e}")

        # Multiple threads ile parallel increment
        threads = []
        for counter in counters:
            thread = threading.Thread(target=increment_counter, args=(counter, 500))
            threads.append(thread)
            thread.start()

        # Tüm thread'lerin bitmesini bekle
        for thread in threads:
            thread.join()

        # Final değerleri göster
        print(f"\n📊 Final counter values:")
        for counter in counters:
            try:
                value = self.cluster.get(f"counter:{counter}")
                print(f"   {counter}: {value}")
            except Exception as e:
                print(f"   ❌ Error reading {counter}: {e}")

    def distributed_queue_example(self):
        """
        Distributed queue example using lists
        """
        print("\n📋 Distributed Queue Example")
        print("=" * 35)

        queue_name = "task_queue"

        # Producer - queue'ye task ekle
        tasks = [
            {"id": 1, "type": "email", "recipient": "user@example.com", "priority": "high"},
            {"id": 2, "type": "report", "data": "monthly_sales", "priority": "medium"},
            {"id": 3, "type": "backup", "database": "users", "priority": "low"},
            {"id": 4, "type": "email", "recipient": "admin@example.com", "priority": "high"},
        ]

        print(f"📤 Adding tasks to queue:")
        for task in tasks:
            try:
                task_json = json.dumps(task)
                self.cluster.lpush(queue_name, task_json)
                print(f"   ➕ Added task {task['id']}: {task['type']}")
            except Exception as e:
                print(f"   ❌ Error adding task: {e}")

        # Consumer - queue'den task işle
        print(f"\n📥 Processing tasks from queue:")
        while True:
            try:
                # Blocking pop with timeout
                result = self.cluster.brpop(queue_name, timeout=2)
                if result:
                    queue_name_result, task_json = result
                    task = json.loads(task_json)
                    print(f"   🔄 Processing task {task['id']}: {task['type']} (priority: {task['priority']})")

                    # Simulate task processing
                    time.sleep(0.5)
                    print(f"   ✅ Completed task {task['id']}")
                else:
                    print(f"   📭 Queue is empty")
                    break
            except Exception as e:
                print(f"   ❌ Error processing queue: {e}")
                break

def demo_redis_cluster():
    """
    Redis Cluster comprehensive demo
    """
    print("🚀 Redis Cluster Comprehensive Demo")
    print("=" * 50)

    # Cluster manager
    cluster_manager = RedisClusterManager()

    if not cluster_manager.cluster:
        print("❌ Cannot connect to Redis Cluster. Make sure cluster is running.")
        return

    # Cluster bilgileri
    print("\n📊 Cluster Information:")
    cluster_info = cluster_manager.cluster_info()
    print(f"   Total nodes: {cluster_info.get('total_nodes', 0)}")
    print(f"   Masters: {cluster_info.get('masters', 0)}")
    print(f"   Slaves: {cluster_info.get('slaves', 0)}")

    # Scaling demo
    scaling_results = cluster_manager.cluster_scaling_demo()

    # Application examples
    app = RedisClusterApplication(cluster_manager)

    # Distributed cache
    app.distributed_cache_example()

    # Distributed counters
    app.distributed_counter_example()

    # Distributed queue
    app.distributed_queue_example()

    print("\n✅ Redis Cluster demo completed!")

if __name__ == "__main__":
    demo_redis_cluster()
```

## 🚀 Production Deployment

### Kubernetes Deployment

```yaml
# kubernetes/redis-cluster.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: redis-system
spec:
  serviceName: redis-cluster
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
        - name: redis
          image: redis:7.2-alpine
          ports:
            - containerPort: 6379
              name: client
            - containerPort: 16379
              name: gossip
          command:
            - redis-server
            - /etc/redis/redis.conf
          env:
            - name: POD_IP
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
          volumeMounts:
            - name: conf
              mountPath: /etc/redis/
            - name: data
              mountPath: /data
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
      volumes:
        - name: conf
          configMap:
            name: redis-cluster-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 10Gi
        storageClassName: fast-ssd

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-cluster-config
  namespace: redis-system
data:
  redis.conf: |
    port 6379
    bind 0.0.0.0
    protected-mode no
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    appendonly yes
    appendfsync everysec
    maxmemory 1gb
    maxmemory-policy allkeys-lru

---
apiVersion: v1
kind: Service
metadata:
  name: redis-cluster
  namespace: redis-system
spec:
  type: ClusterIP
  clusterIP: None
  ports:
    - port: 6379
      targetPort: 6379
      name: client
    - port: 16379
      targetPort: 16379
      name: gossip
  selector:
    app: redis-cluster
```

### Monitoring Setup

```yaml
# monitoring/redis-exporter.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-exporter
  namespace: redis-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-exporter
  template:
    metadata:
      labels:
        app: redis-exporter
    spec:
      containers:
        - name: redis-exporter
          image: oliver006/redis_exporter:latest
          ports:
            - containerPort: 9121
          env:
            - name: REDIS_ADDR
              value: "redis://redis-cluster:6379"
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "128Mi"
              cpu: "100m"

---
apiVersion: v1
kind: Service
metadata:
  name: redis-exporter
  namespace: redis-system
  labels:
    app: redis-exporter
spec:
  ports:
    - port: 9121
      targetPort: 9121
  selector:
    app: redis-exporter
```

## 📊 Monitoring ve Alerting

### Prometheus Rules

```yaml
# monitoring/redis-cluster-rules.yaml
groups:
  - name: redis-cluster
    rules:
      - alert: RedisClusterDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis cluster node is down"
          description: "Redis cluster node {{ $labels.instance }} has been down for more than 1 minute"

      - alert: RedisClusterHighMemoryUsage
        expr: redis_memory_used_bytes / redis_memory_max_bytes * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis cluster high memory usage"
          description: "Redis cluster node {{ $labels.instance }} memory usage is above 80%"

      - alert: RedisClusterSlowQueries
        expr: redis_slowlog_length > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis cluster has slow queries"
          description: "Redis cluster node {{ $labels.instance }} has {{ $value }} slow queries"
```

## ✅ Checklist

Bu bölümü tamamladıktan sonra:

- [ ] Redis Cluster architecture'ını anlıyorum
- [ ] Multi-node cluster kurabiliyorum
- [ ] Data sharding ve hash slots kullanabiliyorum
- [ ] Failover scenarios'ları handle edebiliyorum
- [ ] Cluster management operations yapabiliyorum
- [ ] Production deployment uygulayabiliyorum
- [ ] Performance monitoring setup edebiliyorum
- [ ] Scaling strategies planlayabiliyorum

## ⚠️ Production Best Practices

### 1. Cluster Sizing

- **Minimum 6 nodes**: 3 master + 3 slave
- **Odd number of masters**: Split-brain prevention
- **RAM sizing**: 50% of available memory for Redis
- **CPU**: 2-4 cores per node optimal

### 2. Network Configuration

- **Low latency**: <1ms between nodes ideal
- **Dedicated network**: Cluster traffic isolation
- **Firewall rules**: 6379 (client) + 16379 (cluster bus)

### 3. Monitoring Metrics

- **Cluster health**: All nodes connected
- **Memory usage**: <80% recommended
- **Network latency**: <5ms cluster bus
- **Slow queries**: Monitor slowlog

## 🔗 İlgili Bölümler

- **Önceki**: [Redis Streams](05-streams.md)
- **Sonraki**: [Integration Examples](../05-integration/README.md)
- **İlgili**: [Elasticsearch Production](../04-elasticsearch/04-production-deployment.md)

---

**Sonraki Adım**: Tüm teknolojilerin entegrasyonu için [Integration Examples](../05-integration/README.md) bölümüne geçin! 🚀
