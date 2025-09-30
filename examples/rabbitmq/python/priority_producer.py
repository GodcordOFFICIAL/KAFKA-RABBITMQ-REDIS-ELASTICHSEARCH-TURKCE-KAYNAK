"""
RabbitMQ Priority Queue Producer
===============================

Bu script farklı öncelik seviyeli mesajları demonstre eder.

Priority Levels:
- 0-10 arası priority (10 en yüksek)
- Yüksek priority mesajlar önce işlenir
- Aynı priority'deki mesajlar FIFO

Kullanım:
    python priority_producer.py
    python priority_producer.py custom "Urgent task" 9
    python priority_producer.py batch
"""

import pika
import json
import time
import random
import argparse
from datetime import datetime
from enum import Enum


class TaskPriority(Enum):
    CRITICAL = 10
    HIGH = 8
    MEDIUM = 5
    LOW = 2
    BACKGROUND = 0


class PriorityProducer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        
        # Publisher confirms
        self.channel.confirm_delivery()
        
        self.setup_priority_system()
        self.sent_count = 0
        self.confirmed_count = 0
        self.priority_stats = {i: 0 for i in range(11)}  # 0-10 priority levels
    
    def setup_priority_system(self):
        """Priority sistemini kurar"""
        print("🔧 Priority sistemi kuruluyor...")
        
        # Main exchange
        self.channel.exchange_declare(
            exchange='priority_tasks',
            exchange_type='direct',
            durable=True
        )
        
        # Priority queue (0-10 priority levels)
        self.channel.queue_declare(
            queue='task_queue',
            durable=True,
            arguments={
                'x-max-priority': 10  # 0-10 arası priority
            }
        )
        
        # Dead letter setup for failed high priority tasks
        self.channel.exchange_declare(
            exchange='priority_tasks_dlx',
            exchange_type='direct',
            durable=True
        )
        
        self.channel.queue_declare(
            queue='failed_priority_tasks',
            durable=True
        )
        
        # Urgent tasks queue (only priority 9-10)
        self.channel.queue_declare(
            queue='urgent_tasks',
            durable=True,
            arguments={
                'x-max-priority': 10,
                'x-dead-letter-exchange': 'priority_tasks_dlx',
                'x-dead-letter-routing-key': 'failed_urgent'
            }
        )
        
        # Background tasks queue (only priority 0-2)
        self.channel.queue_declare(
            queue='background_tasks',
            durable=True,
            arguments={
                'x-max-priority': 2,  # Lower max priority
                'x-message-ttl': 3600000  # 1 hour TTL
            }
        )
        
        # Bindings
        bindings = [
            ('priority_tasks', 'task_queue', 'task'),
            ('priority_tasks', 'urgent_tasks', 'urgent'),
            ('priority_tasks', 'background_tasks', 'background'),
            ('priority_tasks_dlx', 'failed_priority_tasks', 'failed_urgent')
        ]
        
        for exchange, queue, routing_key in bindings:
            self.channel.queue_bind(
                exchange=exchange,
                queue=queue,
                routing_key=routing_key
            )
        
        print("✅ Priority sistemi hazır!")
    
    def send_task(self, task_name, priority=5, task_data=None, routing_key='task'):
        """Öncelikli task gönderir"""
        # Priority validation
        priority = max(0, min(10, priority))  # 0-10 arası sınırla
        
        task = {
            'name': task_name,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'task_id': f"task_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            'routing_key': routing_key,
            'data': task_data or {}
        }
        
        # Task type ve metadata
        task_metadata = self.get_task_metadata(task_name, priority)
        task.update(task_metadata)
        
        properties = pika.BasicProperties(
            priority=priority,
            delivery_mode=2,
            message_id=task['task_id'],
            timestamp=int(datetime.now().timestamp()),
            headers={
                'task_type': task_name,
                'priority_level': priority,
                'department': task_metadata.get('department', 'general'),
                'estimated_duration': task_metadata.get('estimated_duration', 60),
                'created_at': datetime.now().isoformat()
            }
        )
        
        try:
            result = self.channel.basic_publish(
                exchange='priority_tasks',
                routing_key=routing_key,
                body=json.dumps(task, indent=2),
                properties=properties,
                mandatory=True
            )
            
            self.sent_count += 1
            self.priority_stats[priority] += 1
            
            if result:
                self.confirmed_count += 1
                
                # Priority emoji ve info
                priority_info = self.get_priority_info(priority)
                print(f"{priority_info['emoji']} P{priority}: {task_name} → {routing_key} ({priority_info['level']})")
                return True
            else:
                print(f"❌ Not confirmed: {task_name}")
                return False
                
        except Exception as e:
            print(f"💥 Send error: {str(e)}")
            return False
    
    def get_task_metadata(self, task_name, priority):
        """Task metadata'sını oluşturur"""
        task_name_lower = task_name.lower()
        
        # Department assignment
        if any(word in task_name_lower for word in ['security', 'alert', 'breach', 'incident']):
            department = 'security'
            estimated_duration = 30
        elif any(word in task_name_lower for word in ['payment', 'billing', 'financial']):
            department = 'finance'
            estimated_duration = 120
        elif any(word in task_name_lower for word in ['backup', 'maintenance', 'cleanup']):
            department = 'operations'
            estimated_duration = 300
        elif any(word in task_name_lower for word in ['email', 'notification', 'newsletter']):
            department = 'marketing'
            estimated_duration = 60
        else:
            department = 'general'
            estimated_duration = 90
        
        # Priority-based adjustments
        if priority >= 9:
            category = 'critical'
            estimated_duration = min(estimated_duration, 60)  # Critical tasks max 1 hour
        elif priority >= 7:
            category = 'high'
        elif priority >= 4:
            category = 'medium'
        else:
            category = 'low'
            estimated_duration *= 2  # Low priority tasks can take longer
        
        return {
            'department': department,
            'category': category,
            'estimated_duration': estimated_duration
        }
    
    def get_priority_info(self, priority):
        """Priority bilgilerini döndürür"""
        if priority >= 9:
            return {'emoji': '🔴', 'level': 'CRITICAL', 'color': 'red'}
        elif priority >= 7:
            return {'emoji': '🟠', 'level': 'HIGH', 'color': 'orange'}
        elif priority >= 4:
            return {'emoji': '🟡', 'level': 'MEDIUM', 'color': 'yellow'}
        elif priority >= 2:
            return {'emoji': '🟢', 'level': 'LOW', 'color': 'green'}
        else:
            return {'emoji': '🔵', 'level': 'BACKGROUND', 'color': 'blue'}
    
    def demo_priority_tasks(self):
        """Priority demo gösterir"""
        print("\n🎯 Priority Task Demo başlıyor...")
        print("=" * 60)
        
        # Mixed priority tasks
        tasks = [
            ("Database Backup", 1, 'background'),
            ("Critical Security Alert", 10, 'urgent'),
            ("User Registration Email", 3, 'task'),
            ("System Emergency Shutdown", 10, 'urgent'),
            ("Daily Newsletter Send", 1, 'background'),
            ("Payment Processing Failed", 9, 'urgent'),
            ("Log File Cleanup", 0, 'background'),
            ("Password Reset Request", 6, 'task'),
            ("Server Overload Alert", 9, 'urgent'),
            ("Weekly Report Generation", 2, 'task'),
            ("Data Center Fire Alert", 10, 'urgent'),
            ("Cache Warm-up Task", 1, 'background'),
            ("User Profile Update", 4, 'task'),
            ("Security Breach Detected", 10, 'urgent'),
            ("Routine Maintenance", 2, 'background')
        ]
        
        print("📤 Tasks gönderiliyor (karışık priority sırasında)...")
        
        # Shuffle to show priority ordering works
        random.shuffle(tasks)
        
        for i, (task_name, priority, routing_key) in enumerate(tasks, 1):
            print(f"   {i:2d}. ", end="")
            self.send_task(task_name, priority, routing_key=routing_key)
            time.sleep(0.2)  # Small delay to see individual sends
        
        print("\n" + "=" * 60)
        self.print_send_statistics()
        
        print(f"\n🎯 Consumer priority sırasına göre işleyecek:")
        print(f"   1. CRITICAL (P10): Emergency, Security Breach")
        print(f"   2. HIGH (P9): Payment Failed, Server Overload")
        print(f"   3. MEDIUM (P4-6): Password Reset, Profile Update")
        print(f"   4. LOW (P2-3): Report, Registration Email")
        print(f"   5. BACKGROUND (P0-1): Backup, Cleanup, Newsletter")
    
    def send_burst_priority_test(self):
        """Burst priority test"""
        print("\n💥 Burst Priority Test...")
        
        # Hızlı ardışık gönderim
        burst_tasks = []
        for i in range(20):
            priority = random.randint(0, 10)
            task_name = f"Burst Task {i+1}"
            burst_tasks.append((task_name, priority))
        
        # Sort by priority to show expected processing order
        expected_order = sorted(burst_tasks, key=lambda x: x[1], reverse=True)
        
        print("📤 20 task hızlı gönderim...")
        for task_name, priority in burst_tasks:
            self.send_task(task_name, priority, routing_key='task')
            time.sleep(0.05)  # Very fast sending
        
        print(f"\n📊 Expected Processing Order (first 10):")
        for i, (task_name, priority) in enumerate(expected_order[:10], 1):
            priority_info = self.get_priority_info(priority)
            print(f"   {i:2d}. {priority_info['emoji']} P{priority}: {task_name}")
    
    def send_department_tasks(self):
        """Department bazlı tasks"""
        print("\n🏢 Department Tasks...")
        
        department_tasks = [
            # Security Department (High Priority)
            ("Intrusion Detection Alert", 9, 'urgent'),
            ("Access Control Violation", 8, 'urgent'), 
            ("Security Audit Report", 6, 'task'),
            
            # Finance Department (Medium-High Priority)
            ("Payment Gateway Down", 9, 'urgent'),
            ("Transaction Reconciliation", 7, 'task'),
            ("Monthly Financial Report", 5, 'task'),
            
            # Operations (Varied Priority)
            ("Server Maintenance Window", 7, 'task'),
            ("Database Optimization", 4, 'task'),
            ("Log Rotation", 1, 'background'),
            
            # Marketing (Low-Medium Priority)
            ("Campaign Email Send", 3, 'task'),
            ("Social Media Post", 2, 'task'),
            ("Analytics Report", 1, 'background')
        ]
        
        print("📤 Department tasks gönderiliyor...")
        for task_name, priority, routing_key in department_tasks:
            self.send_task(task_name, priority, routing_key=routing_key)
            time.sleep(0.3)
        
        print("🏢 Department tasks gönderildi")
    
    def monitor_queues(self):
        """Queue durumlarını gösterir"""
        try:
            queues = [
                ('task_queue', 'Main Task Queue'),
                ('urgent_tasks', 'Urgent Tasks (P9-10)'),
                ('background_tasks', 'Background Tasks (P0-2)'),
                ('failed_priority_tasks', 'Failed Priority Tasks')
            ]
            
            print(f"\n📊 Queue Durumu ({datetime.now().strftime('%H:%M:%S')}):")
            print("-" * 50)
            
            for queue_name, description in queues:
                try:
                    result = self.channel.queue_declare(queue=queue_name, passive=True)
                    count = result.method.message_count
                    
                    if count > 0:
                        if 'urgent' in queue_name.lower() and count > 5:
                            emoji = "🚨"
                        elif count > 10:
                            emoji = "📦"
                        else:
                            emoji = "📝"
                    else:
                        emoji = "📭"
                    
                    print(f"   {emoji} {description}: {count} mesaj")
                    
                except Exception as e:
                    print(f"   ❌ {description}: Error - {str(e)}")
            
        except Exception as e:
            print(f"❌ Queue monitoring error: {str(e)}")
    
    def print_send_statistics(self):
        """Gönderim istatistiklerini yazdırır"""
        print(f"📊 Gönderim İstatistikleri:")
        print(f"   📤 Total Sent: {self.sent_count}")
        print(f"   ✅ Confirmed: {self.confirmed_count}")
        print(f"   📈 Success Rate: {(self.confirmed_count / self.sent_count) * 100:.1f}%")
        
        print(f"\n🎯 Priority Dağılımı:")
        for priority in range(10, -1, -1):  # 10'dan 0'a
            count = self.priority_stats[priority]
            if count > 0:
                priority_info = self.get_priority_info(priority)
                print(f"   {priority_info['emoji']} P{priority} ({priority_info['level']}): {count} task")
    
    def close(self):
        self.connection.close()


def main():
    parser = argparse.ArgumentParser(description='RabbitMQ Priority Producer')
    parser.add_argument('mode', nargs='?', default='demo',
                       choices=['demo', 'custom', 'burst', 'department', 'monitor'],
                       help='Çalışma modu')
    parser.add_argument('task_name', nargs='?', default='Custom Priority Task',
                       help='Task adı')
    parser.add_argument('priority', nargs='?', type=int, default=5,
                       help='Priority (0-10)')
    parser.add_argument('--routing-key', default='task',
                       choices=['task', 'urgent', 'background'],
                       help='Routing key')
    
    args = parser.parse_args()
    
    producer = PriorityProducer()
    
    try:
        if args.mode == 'demo':
            producer.demo_priority_tasks()
        elif args.mode == 'custom':
            producer.send_task(
                args.task_name, 
                args.priority,
                routing_key=args.routing_key
            )
        elif args.mode == 'burst':
            producer.send_burst_priority_test()
        elif args.mode == 'department':
            producer.send_department_tasks()
        elif args.mode == 'monitor':
            producer.monitor_queues()
        
        # Her durumda queue durumunu göster
        if args.mode != 'monitor':
            time.sleep(1)
            producer.monitor_queues()
            
    finally:
        producer.close()


if __name__ == "__main__":
    main()