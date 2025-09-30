#!/usr/bin/env python3
"""
RabbitMQ Fanout Exchange Consumer
Fanout exchange ile broadcast notification consumption örneği.
"""

import pika
import json
import sys
import signal
import time
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationConsumer:
    def __init__(self, consumer_name, notification_types=None, min_priority='low', host='localhost', port=5672, username='admin', password='admin123'):
        """Notification Consumer initialization"""
        self.consumer_name = consumer_name
        self.notification_types = notification_types or []  # Empty list = all types
        self.min_priority = min_priority
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.queue_name = None
        self.processed_count = 0
        
        # Priority levels
        self.priority_levels = {
            'low': 1,
            'normal': 5,
            'high': 8,
            'critical': 10
        }
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Graceful shutdown"""
        logger.info(f"\n🔴 [{self.consumer_name}] Consumer stopping...")
        logger.info(f"📊 Processed {self.processed_count} notifications")
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
                exchange='notifications',
                exchange_type='fanout',
                durable=True
            )
            
            # Exclusive queue (her consumer'ın kendi queue'su)
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue
            
            # Fanout exchange'e bind et
            self.channel.queue_bind(
                exchange='notifications',
                queue=self.queue_name
            )
            
            logger.info(f"✅ [{self.consumer_name}] Connected to RabbitMQ")
            logger.info(f"🔗 [{self.consumer_name}] Bound to fanout exchange")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def callback(self, ch, method, properties, body):
        """Bildirim işle"""
        try:
            notification = json.loads(body)
            
            # Type filtering (eğer belirtilmişse)
            if (self.notification_types and 
                notification['type'] not in self.notification_types):
                return
            
            # Priority filtering
            notif_priority = notification.get('priority', 'normal')
            if (self.priority_levels.get(notif_priority, 0) < 
                self.priority_levels.get(self.min_priority, 0)):
                return
            
            self.processed_count += 1
            
            # Display notification
            self._display_notification(notification)
            
            # Simulate processing based on type
            self._process_notification(notification)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
    
    def _display_notification(self, notification):
        """Bildirimi görüntüle"""
        type_emoji = {
            'system': '⚙️',
            'security': '🔒',
            'promotion': '🎉',
            'alert': '🚨',
            'info': 'ℹ️',
            'maintenance': '🔧',
            'update': '🔄'
        }.get(notification['type'], '📢')
        
        priority_emoji = {
            'low': '🟢',
            'normal': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }.get(notification.get('priority', 'normal'), '🟡')
        
        print(f"\n{type_emoji}{priority_emoji} [{self.consumer_name}] {notification['title']}")
        print(f"💬 {notification['message']}")
        print(f"⏰ {notification['timestamp']}")
        print(f"🏷️ Type: {notification['type']} | Priority: {notification.get('priority', 'normal')}")
        
        if notification.get('data'):
            print(f"📋 Data: {notification['data']}")
    
    def _process_notification(self, notification):
        """Bildirim tipine göre işlem yap"""
        notif_type = notification['type']
        priority = notification.get('priority', 'normal')
        
        if notif_type == 'security':
            print("🛑 SECURITY ACTION: Logging security event and alerting admin")
            if priority == 'critical':
                print("📞 ESCALATION: Calling security team immediately")
                
        elif notif_type == 'system':
            print("🔍 SYSTEM ACTION: Checking system health and logging event")
            if priority in ['high', 'critical']:
                print("📊 MONITORING: Increasing system monitoring frequency")
                
        elif notif_type == 'maintenance':
            print("🔧 MAINTENANCE ACTION: Scheduling maintenance tasks")
            
        elif notif_type == 'promotion':
            print("🎁 PROMOTION ACTION: Displaying promotion banner")
            
        elif notif_type == 'alert':
            print("⚠️ ALERT ACTION: Triggering alert protocols")
            if priority == 'critical':
                print("🚨 EMERGENCY: Activating emergency response")
                
        elif notif_type == 'info':
            print("📄 INFO ACTION: Logging information for user display")
            
        elif notif_type == 'update':
            print("🔄 UPDATE ACTION: Processing system update")
    
    def start_consuming(self):
        """Bildirim dinlemeye başla"""
        if not self.channel:
            self.connect()
            
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback,
            auto_ack=True
        )
        
        filter_info = []
        if self.notification_types:
            filter_info.append(f"types: {', '.join(self.notification_types)}")
        filter_info.append(f"min priority: {self.min_priority}")
        
        filter_msg = f" (filtering: {'; '.join(filter_info)})" if filter_info else ""
        
        print(f"👂 [{self.consumer_name}] Listening for notifications{filter_msg}")
        print("🔴 Press CTRL+C to exit\n")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.signal_handler(None, None)

def show_usage():
    """Kullanım örneklerini göster"""
    print("\n📋 Usage examples:")
    print("  python fanout_exchange_consumer.py mobile_app")
    print("  python fanout_exchange_consumer.py web_app --types system security")
    print("  python fanout_exchange_consumer.py desktop_app --priority high")
    print("  python fanout_exchange_consumer.py api_service --types alert system --priority normal")
    print("\n🏷️ Available types: system, security, promotion, alert, info, maintenance, update")
    print("📊 Available priorities: low, normal, high, critical")

def main():
    if len(sys.argv) < 2:
        print("Usage: python fanout_exchange_consumer.py <consumer_name> [options]")
        print("Options:")
        print("  --types TYPE1 TYPE2 ...    Filter by notification types")
        print("  --priority LEVEL           Minimum priority level (low, normal, high, critical)")
        show_usage()
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    consumer_name = args[0]
    notification_types = []
    min_priority = 'low'
    
    i = 1
    while i < len(args):
        if args[i] == '--types':
            i += 1
            while i < len(args) and not args[i].startswith('--'):
                notification_types.append(args[i])
                i += 1
        elif args[i] == '--priority' and i + 1 < len(args):
            min_priority = args[i + 1]
            i += 2
        else:
            i += 1
    
    # Validate priority
    valid_priorities = ['low', 'normal', 'high', 'critical']
    if min_priority not in valid_priorities:
        print(f"❌ Invalid priority: {min_priority}")
        print(f"✅ Valid priorities: {', '.join(valid_priorities)}")
        sys.exit(1)
    
    # Validate types
    valid_types = ['system', 'security', 'promotion', 'alert', 'info', 'maintenance', 'update']
    invalid_types = set(notification_types) - set(valid_types)
    if invalid_types:
        print(f"❌ Invalid notification types: {', '.join(invalid_types)}")
        print(f"✅ Valid types: {', '.join(valid_types)}")
        sys.exit(1)
    
    consumer = NotificationConsumer(
        consumer_name, 
        notification_types if notification_types else None,
        min_priority
    )
    consumer.start_consuming()

if __name__ == '__main__':
    main()