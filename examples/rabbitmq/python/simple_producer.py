#!/usr/bin/env python3
"""
RabbitMQ Simple Producer
Bu dosya temel RabbitMQ producer işlemlerini gösterir.
"""

import pika
import sys
import json
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleProducer:
    def __init__(self, host='localhost', port=5672, username='admin', password='admin123'):
        """RabbitMQ Producer initialization"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        
    def connect(self):
        """RabbitMQ bağlantısı oluştur"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            logger.info("✅ RabbitMQ'ya bağlandı")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Bağlantı hatası: {e}")
            raise
    
    def send_simple_message(self, message):
        """Basit mesaj gönder"""
        if not self.channel:
            self.connect()
            
        # Queue declare et (idempotent)
        self.channel.queue_declare(queue='hello', durable=True)
        
        # Mesaj verilerini hazırla
        message_data = {
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'sender': 'simple_producer',
            'type': 'simple_message'
        }
        
        # Mesaj gönder
        self.channel.basic_publish(
            exchange='',
            routing_key='hello',
            body=json.dumps(message_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mesajı persistent yap
                content_type='application/json'
            )
        )
        
        logger.info(f"📤 Mesaj gönderildi: {message}")
    
    def close(self):
        """Bağlantıyı kapat"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔒 Bağlantı kapatıldı")

def main():
    producer = SimpleProducer()
    
    try:
        producer.connect()
        
        if len(sys.argv) > 1:
            message = ' '.join(sys.argv[1:])
        else:
            message = "Merhaba RabbitMQ!"
        
        producer.send_simple_message(message)
        
    except Exception as e:
        logger.error(f"❌ Producer hatası: {e}")
    finally:
        producer.close()

if __name__ == '__main__':
    main()