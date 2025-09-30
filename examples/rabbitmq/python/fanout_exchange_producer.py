#!/usr/bin/env python3
"""
RabbitMQ Fanout Exchange Producer
Fanout exchange ile broadcast notification örneği.
"""

import pika
import json
import sys
import time
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationProducer:
    def __init__(self, host='localhost', port=5672, username='admin', password='admin123'):
        """Notification Producer initialization"""
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
            
            # Fanout exchange declare
            self.channel.exchange_declare(
                exchange='notifications',
                exchange_type='fanout',
                durable=True
            )
            
            logger.info("✅ Connected to RabbitMQ")
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def broadcast_notification(self, notification_type, title, message, data=None, priority='normal'):
        """Bildirim yayınla"""
        if not self.channel:
            self.connect()
            
        notification = {
            'type': notification_type,
            'title': title,
            'message': message,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'data': data or {},
            'sender': 'NotificationSystem',
            'id': f"notif_{int(time.time() * 1000)}"
        }
        
        # Fanout exchange - routing key önemli değil
        self.channel.basic_publish(
            exchange='notifications',
            routing_key='',  # Fanout'ta routing key görmezden gelinir
            body=json.dumps(notification),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                priority=self._get_priority_value(priority)
            )
        )
        
        type_emoji = {
            'system': '⚙️',
            'security': '🔒',
            'promotion': '🎉',
            'alert': '🚨',
            'info': 'ℹ️',
            'maintenance': '🔧',
            'update': '🔄'
        }.get(notification_type, '📢')
        
        priority_emoji = {
            'low': '🟢',
            'normal': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }.get(priority, '🟡')
        
        print(f"{type_emoji}{priority_emoji} Broadcast: [{notification_type.upper()}] {title}")
    
    def _get_priority_value(self, priority):
        """Priority string'ini sayısal değere çevir"""
        priority_map = {
            'low': 1,
            'normal': 5,
            'high': 8,
            'critical': 10
        }
        return priority_map.get(priority, 5)
    
    def broadcast_batch_notifications(self, notifications):
        """Batch bildirim yayını"""
        if not self.channel:
            self.connect()
            
        for notif in notifications:
            self.broadcast_notification(
                notif['type'],
                notif['title'],
                notif['message'],
                notif.get('data'),
                notif.get('priority', 'normal')
            )
            time.sleep(0.1)  # Small delay between notifications
    
    def close(self):
        """Bağlantıyı kapat"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔒 Connection closed")

def generate_sample_notifications():
    """Sample bildirimler oluştur"""
    return [
        {
            'type': 'system',
            'title': 'Maintenance Window',
            'message': 'System maintenance will start in 30 minutes. Expected duration: 2 hours.',
            'priority': 'high',
            'data': {
                'maintenance_duration': '2 hours',
                'affected_services': ['api', 'web', 'mobile'],
                'start_time': '02:00 UTC'
            }
        },
        {
            'type': 'security',
            'title': 'Security Alert',
            'message': 'Multiple suspicious login attempts detected from unknown location.',
            'priority': 'critical',
            'data': {
                'ip_address': '192.168.1.100',
                'location': 'Unknown',
                'attempts': 5,
                'time_window': '5 minutes'
            }
        },
        {
            'type': 'promotion',
            'title': 'Flash Sale Started',
            'message': '50% discount on all premium features for the next 2 hours!',
            'priority': 'normal',
            'data': {
                'discount_percentage': 50,
                'duration_hours': 2,
                'applicable_items': ['premium_features', 'enterprise_plans']
            }
        },
        {
            'type': 'alert',
            'title': 'High Resource Usage',
            'message': 'Server CPU usage exceeded 90% threshold. Immediate attention required.',
            'priority': 'high',
            'data': {
                'cpu_usage': 95,
                'memory_usage': 87,
                'server_id': 'web-01',
                'threshold': 90
            }
        },
        {
            'type': 'info',
            'title': 'New Feature Release',
            'message': 'Dark mode is now available in user preferences. Update your app to access.',
            'priority': 'low',
            'data': {
                'feature_name': 'dark_mode',
                'version': '2.1.0',
                'availability': 'all_platforms'
            }
        },
        {
            'type': 'update',
            'title': 'Database Migration Complete',
            'message': 'Database migration to new infrastructure completed successfully.',
            'priority': 'normal',
            'data': {
                'migration_type': 'infrastructure',
                'completion_time': datetime.now().isoformat(),
                'performance_improvement': '25%'
            }
        }
    ]

def main():
    producer = NotificationProducer()
    
    try:
        producer.connect()
        
        if len(sys.argv) > 3:
            # Command line: type title message [priority]
            notif_type = sys.argv[1]
            title = sys.argv[2]
            message = sys.argv[3]
            priority = sys.argv[4] if len(sys.argv) > 4 else 'normal'
            
            producer.broadcast_notification(notif_type, title, message, priority=priority)
        else:
            # Demo notifications
            print("📢 Broadcasting sample notifications...")
            sample_notifications = generate_sample_notifications()
            producer.broadcast_batch_notifications(sample_notifications)
            
            print(f"\n✅ Broadcasted {len(sample_notifications)} notifications")
            print("\n📋 Notification types sent:")
            for notif in sample_notifications:
                priority_indicator = {
                    'low': '🟢',
                    'normal': '🟡',
                    'high': '🟠', 
                    'critical': '🔴'
                }.get(notif['priority'], '🟡')
                print(f"   {priority_indicator} {notif['type']} - {notif['title']}")
            
    except Exception as e:
        logger.error(f"❌ Producer error: {e}")
    finally:
        producer.close()

if __name__ == '__main__':
    main()