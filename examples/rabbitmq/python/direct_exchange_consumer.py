#!/usr/bin/env python3
"""
RabbitMQ Direct Exchange Consumer
Direct exchange ile severity-based log consumption örneği.
"""

import pika
import json
import sys
import signal
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogConsumer:
    def __init__(self, severity_levels, host='localhost', port=5672, username='admin', password='admin123'):
        """Log Consumer initialization"""
        self.severity_levels = severity_levels
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.queue_name = None
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Graceful shutdown"""
        logger.info("\n🔴 Consumer stopping...")
        if self.connection and not self.connection.is_closed:
            self.channel.stop_consuming()
            self.connection.close()
        sys.exit(0)
        
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
            
            # Exchange declare
            self.channel.exchange_declare(
                exchange='direct_logs',
                exchange_type='direct',
                durable=True
            )
            
            # Exclusive queue oluştur
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue
            
            # Her severity için binding
            for severity in self.severity_levels:
                self.channel.queue_bind(
                    exchange='direct_logs',
                    queue=self.queue_name,
                    routing_key=severity
                )
                logger.info(f"🔗 Bound to severity: {severity}")
            
            logger.info("✅ Connected to RabbitMQ")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def callback(self, ch, method, properties, body):
        """Log mesajını işle"""
        try:
            log_data = json.loads(body)
            severity = log_data['severity']
            
            severity_emoji = {
                'info': '💙',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🔥'
            }.get(severity, '📝')
            
            print(f"\n{severity_emoji} [{severity.upper()}] {log_data['timestamp']}")
            print(f"📝 {log_data['message']}")
            print(f"🏠 Source: {log_data['source']}")
            
            # Severity-based processing
            if severity == 'critical':
                print("🚨 CRITICAL ALERT: Immediate action required!")
            elif severity == 'error':
                print("🔍 ERROR: Investigation needed")
            elif severity == 'warning':
                print("👀 WARNING: Monitor situation")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
    
    def start_consuming(self):
        """Log dinlemeye başla"""
        if not self.channel:
            self.connect()
            
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback,
            auto_ack=True
        )
        
        print(f"👂 Listening for [{', '.join(self.severity_levels)}] logs...")
        print("🔴 Press CTRL+C to exit\n")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.signal_handler(None, None)

def main():
    if len(sys.argv) < 2:
        print("Usage: python direct_exchange_consumer.py <severity1> [severity2] [severity3]...")
        print("Examples:")
        print("  python direct_exchange_consumer.py error")
        print("  python direct_exchange_consumer.py error warning")
        print("  python direct_exchange_consumer.py info warning error critical")
        print("\nAvailable severities: info, warning, error, critical")
        sys.exit(1)
    
    severity_levels = sys.argv[1:]
    
    # Validate severity levels
    valid_severities = {'info', 'warning', 'error', 'critical'}
    invalid_severities = set(severity_levels) - valid_severities
    
    if invalid_severities:
        print(f"❌ Invalid severities: {', '.join(invalid_severities)}")
        print(f"✅ Valid severities: {', '.join(valid_severities)}")
        sys.exit(1)
    
    consumer = LogConsumer(severity_levels)
    consumer.start_consuming()

if __name__ == '__main__':
    main()