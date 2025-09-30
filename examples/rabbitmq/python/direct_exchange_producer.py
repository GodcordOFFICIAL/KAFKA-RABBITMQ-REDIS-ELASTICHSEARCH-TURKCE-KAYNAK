#!/usr/bin/env python3
"""
RabbitMQ Direct Exchange Producer
Direct exchange ile severity-based log routing örneği.
"""

import pika
import json
import sys
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogProducer:
    def __init__(self, host='localhost', port=5672, username='admin', password='admin123'):
        """Log Producer initialization"""
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
            
            # Direct exchange declare
            self.channel.exchange_declare(
                exchange='direct_logs',
                exchange_type='direct',
                durable=True
            )
            
            logger.info("✅ Connected to RabbitMQ")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def send_log(self, severity, message):
        """Log mesajı gönder"""
        if not self.channel:
            self.connect()
            
        log_data = {
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'source': 'direct_producer',
            'host': self.host
        }
        
        # Direct exchange'e routing key ile gönder
        self.channel.basic_publish(
            exchange='direct_logs',
            routing_key=severity,  # routing key = severity level
            body=json.dumps(log_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json'
            )
        )
        
        severity_emoji = {
            'info': '💙',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🔥'
        }.get(severity, '📝')
        
        print(f"{severity_emoji} [{severity.upper()}] {message}")
    
    def send_batch_logs(self, logs):
        """Batch log gönderme"""
        if not self.channel:
            self.connect()
            
        for severity, message in logs:
            self.send_log(severity, message)
    
    def close(self):
        """Bağlantıyı kapat"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔒 Connection closed")

def main():
    producer = LogProducer()
    
    try:
        producer.connect()
        
        if len(sys.argv) > 2:
            # Command line arguments: severity message
            severity = sys.argv[1]
            message = ' '.join(sys.argv[2:])
            producer.send_log(severity, message)
        else:
            # Demo logs
            demo_logs = [
                ('info', 'Application started successfully'),
                ('info', 'User authentication completed'),
                ('warning', 'High memory usage detected (85%)'),
                ('warning', 'Slow database query detected'),
                ('error', 'Database connection failed'),
                ('error', 'Failed to process order #12345'),
                ('critical', 'System running out of disk space'),
                ('critical', 'Security breach detected')
            ]
            
            print("📝 Sending demo logs...")
            producer.send_batch_logs(demo_logs)
            
    except Exception as e:
        logger.error(f"❌ Producer error: {e}")
    finally:
        producer.close()

if __name__ == '__main__':
    main()