# examples/kafka/python/simple_consumer.py
"""
Kafka Consumer örneği - Python implementasyonu

Bu dosya Kafka Consumer'ın Python ile nasıl kullanılacağını gösterir:
- JSON deserialization ile mesaj okuma
- Farklı commit stratejileri (auto, manual, batch)
- Error handling ve recovery
- Consumer lag monitoring
"""

from kafka import KafkaConsumer, TopicPartition
import json
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleConsumer:
    """
    Kafka Consumer wrapper class
    
    Bu sınıf Kafka Consumer'ı wrap ederek kolay kullanım sağlar
    """
    
    def __init__(self, group_id: str, bootstrap_servers: str = 'localhost:9092'):
        """
        Consumer initialization
        
        Args:
            group_id: Consumer group ID
            bootstrap_servers: Kafka broker addresses
        """
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        
        # Base consumer configuration
        self.consumer_config = {
            # Bootstrap servers - Kafka cluster bağlantı noktası
            'bootstrap_servers': [bootstrap_servers],
            
            # Consumer group
            'group_id': group_id,
            'client_id': f'{group_id}-{int(time.time())}',
            
            # Deserialization - JSON deserialization
            'key_deserializer': lambda x: x.decode('utf-8') if x else None,
            'value_deserializer': lambda x: json.loads(x.decode('utf-8')),
            
            # Offset management
            'auto_offset_reset': 'earliest',  # earliest, latest, none
            'enable_auto_commit': False,      # Manuel commit control
            
            # Session management - Consumer group membership
            'session_timeout_ms': 30000,      # 30 saniye
            'heartbeat_interval_ms': 3000,    # 3 saniye
            'max_poll_interval_ms': 300000,   # 5 dakika
            
            # Fetch configuration - Performance tuning
            'fetch_min_bytes': 1024,          # Minimum fetch size
            'fetch_max_wait_ms': 500,         # Maximum wait time
            'max_poll_records': 100           # Records per poll
        }
        
        self.consumer = None
        logger.info(f"✅ Consumer configuration initialized for group: {group_id}")
    
    def _create_consumer(self, auto_commit: bool = False) -> KafkaConsumer:
        """
        Consumer instance oluşturma
        
        Args:
            auto_commit: Enable auto commit
            
        Returns:
            KafkaConsumer: Configured consumer instance
        """
        config = self.consumer_config.copy()
        config['enable_auto_commit'] = auto_commit
        
        if auto_commit:
            config['auto_commit_interval_ms'] = 5000  # 5 saniye auto commit interval
        
        return KafkaConsumer(**config)
    
    def consume_with_auto_commit(self, topics: List[str], 
                               message_handler: Optional[Callable] = None) -> None:
        """
        Otomatik commit ile mesaj tüketme
        
        Avantajları:
        - Simple implementation
        - Automatic offset management
        - Less code required
        
        Dezavantajları:
        - Risk of message loss
        - No control over commit timing
        - Possible duplicate processing
        
        Args:
            topics: List of topic names to subscribe
            message_handler: Custom message processing function
        """
        self.consumer = self._create_consumer(auto_commit=True)
        self.consumer.subscribe(topics)
        
        logger.info(f"🔄 Starting auto-commit consumer for topics: {topics}")
        
        try:
            for message in self.consumer:
                try:
                    if message_handler:
                        message_handler(message)
                    else:
                        self._default_message_processor(message)
                        
                    # Auto commit enabled olduğu için otomatik commit
                    
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    # Auto commit durumunda error handling sınırlı
                    
        except KeyboardInterrupt:
            logger.info("⚠️ Consumer interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in auto-commit consumer: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("✅ Auto-commit consumer closed")
    
    def consume_with_manual_commit(self, topics: List[str],
                                 message_handler: Optional[Callable] = None) -> None:
        """
        Manuel commit ile mesaj tüketme - Daha güvenli
        
        Avantajları:
        - Full control over offset management
        - No message loss risk
        - Transactional processing
        
        Dezavantajları:
        - More complex implementation
        - Manual error handling required
        - Possible duplicate processing on failure
        
        Args:
            topics: List of topic names to subscribe
            message_handler: Custom message processing function
        """
        self.consumer = self._create_consumer(auto_commit=False)
        self.consumer.subscribe(topics)
        
        logger.info(f"🔄 Starting manual-commit consumer for topics: {topics}")
        
        try:
            while True:
                # Poll messages with timeout
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                if not message_batch:
                    continue
                
                # Her partition'daki mesajları işle
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            # Mesajı işle
                            if message_handler:
                                message_handler(message)
                            else:
                                self._default_message_processor(message)
                            
                            # Başarılı işlem sonrası manuel commit
                            self.consumer.commit({
                                topic_partition: message.offset + 1
                            })
                            
                            logger.debug(f"✅ Committed offset {message.offset + 1} " +
                                       f"for partition {message.partition}")
                            
                        except Exception as e:
                            logger.error(f"❌ Error processing message at offset " +
                                       f"{message.offset}: {e}")
                            # Hata durumunda commit yapılmaz, mesaj tekrar işlenir
                            break  # Bu partition için işlemeyi durdur
                            
        except KeyboardInterrupt:
            logger.info("⚠️ Consumer interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in manual-commit consumer: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("✅ Manual-commit consumer closed")
    
    def consume_with_batch_commit(self, topics: List[str],
                                message_handler: Optional[Callable] = None) -> None:
        """
        Batch commit ile mesaj tüketme - Performance optimized
        
        Avantajları:
        - Higher throughput
        - Reduced commit overhead
        - Better performance for high-volume processing
        
        Dezavantajları:
        - Risk of reprocessing batch on failure
        - Less granular error handling
        - Potential message duplication
        
        Args:
            topics: List of topic names to subscribe
            message_handler: Custom message processing function
        """
        self.consumer = self._create_consumer(auto_commit=False)
        self.consumer.subscribe(topics)
        
        logger.info(f"🔄 Starting batch-commit consumer for topics: {topics}")
        
        try:
            while True:
                # Poll messages with timeout
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                if not message_batch:
                    continue
                
                all_processed_successfully = True
                processed_count = 0
                failed_count = 0
                
                # Tüm mesajları işle
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            if message_handler:
                                message_handler(message)
                            else:
                                self._default_message_processor(message)
                            
                            processed_count += 1
                            
                        except Exception as e:
                            logger.error(f"❌ Error processing message at offset " +
                                       f"{message.offset}: {e}")
                            failed_count += 1
                            all_processed_successfully = False
                            # Batch'te hata varsa devam et, sonunda commit yapmayacağız
                
                # Tüm mesajlar başarılı ise batch commit
                if all_processed_successfully and processed_count > 0:
                    try:
                        self.consumer.commit()  # Tüm partition'lar için commit
                        logger.info(f"✅ Batch committed successfully: {processed_count} records")
                    except Exception as e:
                        logger.error(f"❌ Commit failed: {e}")
                elif processed_count > 0:
                    logger.warning(f"⚠️ Batch processing failed, skipping commit. " +
                                 f"Processed: {processed_count}, Failed: {failed_count}")
                    
        except KeyboardInterrupt:
            logger.info("⚠️ Consumer interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in batch-commit consumer: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("✅ Batch-commit consumer closed")
    
    def consume_from_specific_partition(self, topic: str, partition: int,
                                      message_handler: Optional[Callable] = None) -> None:
        """
        Belirli partition'dan mesaj tüketme
        
        Kullanım senaryoları:
        - Specific partition monitoring
        - Manual partition assignment
        - Testing ve debugging
        - Load balancing control
        
        Args:
            topic: Kafka topic name
            partition: Partition number
            message_handler: Custom message processing function
        """
        self.consumer = self._create_consumer(auto_commit=False)
        
        topic_partition = TopicPartition(topic, partition)
        self.consumer.assign([topic_partition])
        
        # Belirli offset'ten başlatma (opsiyonel)
        self.consumer.seek_to_beginning(topic_partition)
        
        logger.info(f"🔄 Starting consumer for partition {partition} of topic {topic}")
        
        try:
            for message in self.consumer:
                try:
                    logger.info(f"📨 Partition {message.partition}, Offset {message.offset}: " +
                              f"{message.key} = {message.value}")
                    
                    if message_handler:
                        message_handler(message)
                    else:
                        self._default_message_processor(message)
                    
                    # Manuel commit
                    self.consumer.commit()
                    
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    
        except KeyboardInterrupt:
            logger.info("⚠️ Consumer interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in partition consumer: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("✅ Partition consumer closed")
    
    def monitor_consumer_lag(self, topics: List[str], interval: int = 10) -> None:
        """
        Consumer lag monitoring - Performance monitoring
        
        Args:
            topics: List of topic names to monitor
            interval: Monitoring interval in seconds
        """
        self.consumer = self._create_consumer(auto_commit=False)
        self.consumer.subscribe(topics)
        
        logger.info(f"📊 Starting consumer lag monitoring for topics: {topics}")
        
        try:
            while True:
                # Bir kez poll yaparak assignment'ı tetikle
                self.consumer.poll(timeout_ms=1000)
                
                # Her partition için lag hesapla
                for partition in self.consumer.assignment():
                    try:
                        # Current position
                        current_offset = self.consumer.position(partition)
                        
                        # End offset (latest available)
                        end_offsets = self.consumer.end_offsets([partition])
                        end_offset = end_offsets[partition]
                        
                        # Lag calculation
                        lag = end_offset - current_offset
                        
                        if lag > 0:
                            logger.warning(f"⚠️ Consumer lag detected:")
                            logger.warning(f"  Topic: {partition.topic}")
                            logger.warning(f"  Partition: {partition.partition}")
                            logger.warning(f"  Current Offset: {current_offset}")
                            logger.warning(f"  End Offset: {end_offset}")
                            logger.warning(f"  Lag: {lag} messages")
                        else:
                            logger.info(f"✅ No lag for {partition.topic}[{partition.partition}]")
                            
                    except Exception as e:
                        logger.error(f"❌ Error calculating lag for {partition}: {e}")
                
                # Bekleme
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("⚠️ Lag monitoring interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in lag monitoring: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("✅ Lag monitoring stopped")
    
    def _default_message_processor(self, message) -> None:
        """
        Default mesaj işleme logic'i
        
        Bu method gerçek uygulamalarda override edilmeli
        
        Args:
            message: Kafka message object
        """
        logger.info(f"🔄 Processing message:")
        logger.info(f"  Topic: {message.topic}")
        logger.info(f"  Partition: {message.partition}")
        logger.info(f"  Offset: {message.offset}")
        logger.info(f"  Key: {message.key}")
        logger.info(f"  Value: {message.value}")
        logger.info(f"  Timestamp: {message.timestamp}")
        logger.info(f"  Headers: {message.headers}")
        logger.info("-" * 50)
        
        # Simulate processing time
        time.sleep(0.1)  # 100ms işlem süresi simülasyonu
        
        # Simulated business logic validation
        if message.value and isinstance(message.value, dict):
            if message.value.get('event_type') == 'error':
                raise RuntimeError("Simulated processing error for error events")
    
    def get_consumer_metrics(self) -> Dict[str, Any]:
        """
        Consumer metrics ve performance bilgileri
        
        Returns:
            Dict: Consumer metrics
        """
        if not self.consumer:
            return {}
        
        metrics = self.consumer.metrics()
        
        # İlgili metrikleri filtrele
        relevant_metrics = {}
        for metric_name, metric_value in metrics.items():
            if any(keyword in metric_name for keyword in [
                'records-consumed-rate', 'records-lag-max', 'fetch-rate',
                'fetch-latency-avg', 'commit-rate'
            ]):
                relevant_metrics[metric_name] = metric_value
        
        return relevant_metrics
    
    def print_metrics(self) -> None:
        """Consumer metrics'leri console'a yazdır"""
        metrics = self.get_consumer_metrics()
        
        if metrics:
            logger.info("📊 Consumer Metrics:")
            for metric_name, metric_value in metrics.items():
                logger.info(f"  {metric_name}: {metric_value}")
        else:
            logger.warning("⚠️ No metrics available (consumer not initialized)")

# Custom message handlers
def order_event_handler(message):
    """Order event'leri için özel handler"""
    order_data = message.value
    logger.info(f"🛒 Processing order event: {order_data.get('event_type')}")
    
    # Order-specific business logic
    if order_data.get('event_type') == 'order_created':
        logger.info(f"✅ New order created: {order_data.get('order_id')}")
    elif order_data.get('event_type') == 'order_cancelled':
        logger.info(f"❌ Order cancelled: {order_data.get('order_id')}")

def user_event_handler(message):
    """User event'leri için özel handler"""
    user_data = message.value
    logger.info(f"👤 Processing user event: {user_data.get('event_type')}")
    
    # User-specific business logic
    if user_data.get('event_type') == 'login':
        logger.info(f"✅ User login: {user_data.get('user_id')}")
    elif user_data.get('event_type') == 'logout':
        logger.info(f"👋 User logout: {user_data.get('user_id')}")

# Demo functions
def demo_auto_commit():
    """Auto commit demo"""
    consumer = SimpleConsumer("demo-auto-group")
    
    logger.info("🔄 Demo: Auto commit consumer")
    
    try:
        consumer.consume_with_auto_commit(['user-events'], user_event_handler)
    except KeyboardInterrupt:
        logger.info("⚠️ Auto commit demo stopped")

def demo_manual_commit():
    """Manual commit demo"""
    consumer = SimpleConsumer("demo-manual-group")
    
    logger.info("🔄 Demo: Manual commit consumer")
    
    try:
        consumer.consume_with_manual_commit(['user-events'], user_event_handler)
    except KeyboardInterrupt:
        logger.info("⚠️ Manual commit demo stopped")

def demo_batch_commit():
    """Batch commit demo"""
    consumer = SimpleConsumer("demo-batch-group")
    
    logger.info("🔄 Demo: Batch commit consumer")
    
    try:
        consumer.consume_with_batch_commit(['user-events'], user_event_handler)
    except KeyboardInterrupt:
        logger.info("⚠️ Batch commit demo stopped")

def demo_lag_monitoring():
    """Lag monitoring demo"""
    consumer = SimpleConsumer("demo-lag-group")
    
    logger.info("📊 Demo: Consumer lag monitoring")
    
    try:
        consumer.monitor_consumer_lag(['user-events'], interval=5)
    except KeyboardInterrupt:
        logger.info("⚠️ Lag monitoring demo stopped")

# Test usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_consumer.py <mode>")
        print("Modes: auto, manual, batch, partition, lag")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    logger.info(f"🚀 Starting Kafka Consumer demo in {mode} mode...")
    
    try:
        if mode == "auto":
            demo_auto_commit()
        elif mode == "manual":
            demo_manual_commit()
        elif mode == "batch":
            demo_batch_commit()
        elif mode == "partition":
            consumer = SimpleConsumer("demo-partition-group")
            consumer.consume_from_specific_partition('user-events', 0, user_event_handler)
        elif mode == "lag":
            demo_lag_monitoring()
        else:
            logger.error(f"❌ Unknown mode: {mode}")
            print("Available modes: auto, manual, batch, partition, lag")
            
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
    
    logger.info("🎉 Consumer demo completed!")