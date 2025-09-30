# examples/kafka/python/simple_producer.py
"""
Kafka Producer örneği - Python implementasyonu

Bu dosya Kafka Producer'ın Python ile nasıl kullanılacağını gösterir:
- JSON serialization ile mesaj gönderme
- Senkron ve asenkron mesaj gönderme
- Error handling ve retry mekanizmaları
- Performance optimization
"""

from kafka import KafkaProducer
import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleProducer:
    """
    Kafka Producer wrapper class
    
    Bu sınıf Kafka Producer'ı wrap ederek kolay kullanım sağlar
    """
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        """
        Producer initialization
        
        Args:
            bootstrap_servers: Kafka broker addresses
        """
        self.producer = KafkaProducer(
            # Bootstrap servers - Kafka cluster bağlantı noktası
            bootstrap_servers=[bootstrap_servers],
            
            # Serialization - JSON kullanarak object serialization
            key_serializer=lambda x: x.encode('utf-8') if x else None,
            value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8'),
            
            # Delivery guarantee - Güvenlik ayarları
            acks='all',  # Tüm replica'lardan ack bekle
            retries=3,   # Retry sayısı
            retry_backoff_ms=1000,  # Retry delay (ms)
            
            # Performance tuning - Performance optimization
            batch_size=16384,      # 16KB batch size
            linger_ms=10,          # Batch bekleme süresi (ms)
            buffer_memory=33554432,  # 32MB buffer
            
            # Compression - Network efficiency
            compression_type='gzip',
            
            # Idempotence - Duplicate prevention
            enable_idempotence=True,
            
            # Additional configurations
            max_request_size=1048576,  # 1MB max request size
            request_timeout_ms=30000,  # 30 saniye timeout
        )
        
        logger.info("✅ Kafka Producer initialized successfully")
    
    def send_message_sync(self, topic: str, key: str, value: Dict[str, Any]) -> bool:
        """
        Senkron mesaj gönderme - Blocking operation
        
        Avantajları:
        - Immediate feedback (başarı/başarısızlık)
        - Simple error handling
        - Guaranteed delivery before return
        
        Dezavantajları:
        - Lower throughput (blocking operation)
        - Higher latency
        
        Args:
            topic: Kafka topic name
            key: Message key (partition routing için)
            value: Message value (JSON serializable object)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Send ve result'ı bekle
            future = self.producer.send(topic, key=key, value=value)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"✅ Message sent successfully:")
            logger.info(f"  Topic: {record_metadata.topic}")
            logger.info(f"  Partition: {record_metadata.partition}")
            logger.info(f"  Offset: {record_metadata.offset}")
            logger.info(f"  Timestamp: {record_metadata.timestamp}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return False
    
    def send_message_async(self, topic: str, key: str, value: Dict[str, Any]) -> None:
        """
        Asenkron mesaj gönderme - Non-blocking operation
        
        Avantajları:
        - Higher throughput (non-blocking)
        - Lower latency
        - Better resource utilization
        
        Dezavantajları:
        - Complex error handling
        - Callback management
        
        Args:
            topic: Kafka topic name
            key: Message key
            value: Message value
        """
        def on_send_success(record_metadata):
            """Başarılı gönderim callback'i"""
            logger.info(f"✅ Message sent to {record_metadata.topic}[{record_metadata.partition}] "
                      f"at offset {record_metadata.offset}")
        
        def on_send_error(excp):
            """Hatalı gönderim callback'i"""
            logger.error(f"❌ Failed to send message: {excp}")
        
        # Asenkron send
        future = self.producer.send(topic, key=key, value=value)
        future.add_callback(on_send_success)
        future.add_errback(on_send_error)
    
    def send_to_partition(self, topic: str, partition: int, 
                         key: str, value: Dict[str, Any]) -> bool:
        """
        Belirli partition'a mesaj gönderme
        
        Kullanım senaryoları:
        - Specific partition'a routing
        - Load balancing control
        - Ordered processing guarantee
        
        Args:
            topic: Kafka topic name
            partition: Target partition number
            key: Message key
            value: Message value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            future = self.producer.send(topic, key=key, value=value, partition=partition)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"✅ Message sent to partition {record_metadata.partition} "
                      f"with offset {record_metadata.offset}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending to partition: {e}")
            return False
    
    def send_batch_messages(self, topic: str, messages: List[Dict[str, Any]]) -> int:
        """
        Batch mesaj gönderme - Performance optimized
        
        Birden fazla mesajı efficient şekilde gönderir
        
        Args:
            topic: Kafka topic name
            messages: List of messages with 'key' and 'value' fields
            
        Returns:
            int: Successfully sent message count
        """
        sent_count = 0
        
        try:
            # Tüm mesajları asenkron gönder
            for msg in messages:
                key = msg.get('key')
                value = msg.get('value')
                
                if value is None:
                    logger.warning(f"⚠️ Skipping message with no value: {msg}")
                    continue
                
                self.send_message_async(topic, key, value)
                sent_count += 1
            
            # Tüm mesajların gönderilmesini bekle
            self.producer.flush()
            logger.info(f"✅ Batch of {sent_count} messages sent successfully")
            
            return sent_count
            
        except Exception as e:
            logger.error(f"❌ Error in batch send: {e}")
            return sent_count
    
    def send_with_custom_headers(self, topic: str, key: str, value: Dict[str, Any], 
                               headers: Dict[str, str]) -> bool:
        """
        Custom headers ile mesaj gönderme
        
        Args:
            topic: Kafka topic name
            key: Message key
            value: Message value
            headers: Custom headers dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Headers'ı byte array'e convert et
            kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]
            
            future = self.producer.send(
                topic, 
                key=key, 
                value=value, 
                headers=kafka_headers
            )
            record_metadata = future.get(timeout=10)
            
            logger.info(f"✅ Message with headers sent to {record_metadata.topic}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending message with headers: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Producer metrics ve performance bilgileri
        
        Returns:
            Dict: Producer metrics
        """
        metrics = self.producer.metrics()
        
        # İlgili metrikleri filtrele
        relevant_metrics = {}
        for metric_name, metric_value in metrics.items():
            if any(keyword in metric_name for keyword in [
                'record-send-rate', 'batch-size-avg', 'compression-rate-avg',
                'buffer-available-bytes', 'record-error-rate'
            ]):
                relevant_metrics[metric_name] = metric_value
        
        return relevant_metrics
    
    def print_metrics(self) -> None:
        """Producer metrics'leri console'a yazdır"""
        metrics = self.get_metrics()
        
        logger.info("📊 Producer Metrics:")
        for metric_name, metric_value in metrics.items():
            logger.info(f"  {metric_name}: {metric_value}")
    
    def close(self):
        """
        Producer'ı güvenli şekilde kapatma
        
        Pending mesajların gönderilmesini bekler ve resources'ları temizler
        """
        try:
            # Pending mesajları gönder
            self.producer.flush()
            
            # Producer'ı kapat
            self.producer.close()
            
            logger.info("✅ Producer closed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error closing producer: {e}")

# Test ve demo functions
def demo_synchronous_send():
    """Senkron send demo"""
    producer = SimpleProducer()
    
    logger.info("📤 Testing synchronous send:")
    
    for i in range(3):
        message = {
            'user_id': f'sync_user_{i}',
            'event_type': 'login',
            'timestamp': int(time.time()),
            'data': {
                'ip_address': f'192.168.1.{i+100}',
                'user_agent': 'Mozilla/5.0'
            }
        }
        
        success = producer.send_message_sync('user-events', f'sync_user_{i}', message)
        if success:
            logger.info(f"✅ Message {i+1} sent successfully")
        
        time.sleep(0.5)  # 500ms bekleme
    
    producer.close()

def demo_asynchronous_send():
    """Asenkron send demo"""
    producer = SimpleProducer()
    
    logger.info("📤 Testing asynchronous send:")
    
    for i in range(5):
        message = {
            'user_id': f'async_user_{i}',
            'event_type': 'page_view',
            'timestamp': int(time.time()),
            'data': {
                'page': f'/product/{i}',
                'duration': i * 1000
            }
        }
        
        producer.send_message_async('user-events', f'async_user_{i}', message)
    
    # Asenkron mesajların gönderilmesini bekle
    time.sleep(2)
    producer.close()

def demo_batch_send():
    """Batch send demo"""
    producer = SimpleProducer()
    
    logger.info("📤 Testing batch send:")
    
    # Batch mesajları hazırla
    messages = []
    for i in range(10):
        message = {
            'key': f'batch_user_{i}',
            'value': {
                'user_id': f'batch_user_{i}',
                'event_type': 'purchase',
                'timestamp': int(time.time()),
                'data': {
                    'product_id': f'product_{i}',
                    'amount': (i + 1) * 25.99
                }
            }
        }
        messages.append(message)
    
    sent_count = producer.send_batch_messages('user-events', messages)
    logger.info(f"📊 Sent {sent_count} messages in batch")
    
    producer.close()

def demo_headers_send():
    """Headers ile send demo"""
    producer = SimpleProducer()
    
    logger.info("📤 Testing send with headers:")
    
    message = {
        'user_id': 'headers_user',
        'event_type': 'special_event',
        'timestamp': int(time.time())
    }
    
    headers = {
        'source': 'python-producer',
        'version': '1.0',
        'correlation-id': '12345-67890',
        'content-type': 'application/json'
    }
    
    success = producer.send_with_custom_headers(
        'user-events', 'headers_user', message, headers
    )
    
    if success:
        logger.info("✅ Message with headers sent successfully")
    
    producer.close()

# Test usage
if __name__ == "__main__":
    logger.info("🚀 Starting Kafka Producer demo...")
    
    try:
        # 1. Senkron mesaj gönderme test
        demo_synchronous_send()
        
        # 2. Asenkron mesaj gönderme test
        demo_asynchronous_send()
        
        # 3. Batch send test
        demo_batch_send()
        
        # 4. Headers send test
        demo_headers_send()
        
        # 5. Metrics demo
        producer = SimpleProducer()
        
        # Birkaç mesaj gönderip metrics'leri göster
        for i in range(5):
            message = {
                'user_id': f'metrics_user_{i}',
                'event_type': 'test',
                'timestamp': int(time.time())
            }
            producer.send_message_async('user-events', f'metrics_user_{i}', message)
        
        time.sleep(1)
        producer.print_metrics()
        producer.close()
        
        logger.info("🎉 Producer demo completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("⚠️ Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")