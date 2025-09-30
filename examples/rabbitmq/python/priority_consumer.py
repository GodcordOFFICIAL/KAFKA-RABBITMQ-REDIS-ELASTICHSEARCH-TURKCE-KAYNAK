"""
RabbitMQ Priority Queue Consumer
===============================

Bu script priority queue'dan mesajları priority sırasına göre işler.

Özellikler:
- Priority-based processing
- Statistics tracking
- Processing time simulation
- Graceful shutdown

Kullanım:
    python priority_consumer.py
    python priority_consumer.py --queue urgent_tasks
    python priority_consumer.py --fast
"""

import pika
import json
import time
import random
import signal
import sys
import argparse
from datetime import datetime
from collections import defaultdict


class PriorityConsumer:
    def __init__(self, queue_name='task_queue', fast_mode=False):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.queue_name = queue_name
        self.fast_mode = fast_mode
        
        # Statistics
        self.stats = {
            'processed': 0,
            'failed': 0,
            'priority_counts': defaultdict(int),
            'department_counts': defaultdict(int),
            'processing_times': [],
            'start_time': datetime.now(),
            'last_priority': None
        }
        
        # Processing order tracking
        self.processing_order = []
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
    
    def signal_handler(self, sig, frame):
        """Graceful shutdown handler"""
        print(f"\n🛑 Shutdown signal alındı")
        self.running = False
        self.channel.stop_consuming()
    
    def get_priority_info(self, priority):
        """Priority bilgilerini döndürür"""
        if priority >= 9:
            return {'emoji': '🔴', 'level': 'CRITICAL', 'process_time': 0.2}
        elif priority >= 7:
            return {'emoji': '🟠', 'level': 'HIGH', 'process_time': 0.5}
        elif priority >= 4:
            return {'emoji': '🟡', 'level': 'MEDIUM', 'process_time': 1.0}
        elif priority >= 2:
            return {'emoji': '🟢', 'level': 'LOW', 'process_time': 2.0}
        else:
            return {'emoji': '🔵', 'level': 'BACKGROUND', 'process_time': 3.0}
    
    def simulate_task_processing(self, task, priority):
        """Task işleme simülasyonu"""
        task_name = task.get('name', 'Unknown')
        department = task.get('department', 'general')
        estimated_duration = task.get('estimated_duration', 60)
        
        # Priority-based processing time
        priority_info = self.get_priority_info(priority)
        base_time = priority_info['process_time']
        
        if self.fast_mode:
            base_time *= 0.1  # 10x faster in fast mode
        
        # Add some randomness
        processing_time = base_time * random.uniform(0.5, 1.5)
        
        # Department-specific processing
        if department == 'security':
            # Security tasks need immediate attention
            processing_time *= 0.7
        elif department == 'finance':
            # Financial tasks need careful processing
            processing_time *= 1.2
        elif department == 'operations':
            # Operations tasks vary widely
            processing_time *= random.uniform(0.8, 1.5)
        
        # Task-specific processing
        task_name_lower = task_name.lower()
        if any(word in task_name_lower for word in ['emergency', 'critical', 'alert']):
            processing_time *= 0.5  # Fast emergency processing
        elif any(word in task_name_lower for word in ['backup', 'cleanup', 'maintenance']):
            processing_time *= 2.0  # Slower background tasks
        
        # Simulate processing
        time.sleep(processing_time)
        
        return processing_time
    
    def process_task(self, channel, method, properties, body):
        """Task'ı işler"""
        process_start = time.time()
        
        try:
            task = json.loads(body)
            task_id = task.get('task_id', 'Unknown')[:12]
            task_name = task.get('name', 'Unknown Task')
            priority = task.get('priority', 0)
            department = task.get('department', 'general')
            timestamp = task.get('timestamp', 'Unknown')
            
            # Headers
            headers = properties.headers or {}
            estimated_duration = headers.get('estimated_duration', 60)
            
            # Priority info
            priority_info = self.get_priority_info(priority)
            
            print(f"\n{priority_info['emoji']} Processing P{priority} Task:")
            print(f"   🆔 ID: {task_id}")
            print(f"   📋 Name: {task_name}")
            print(f"   🏢 Dept: {department}")
            print(f"   ⏱️ Est Duration: {estimated_duration}s")
            print(f"   📅 Created: {timestamp[:19]}")
            
            # Priority order check
            if self.stats['last_priority'] is not None:
                if priority > self.stats['last_priority']:
                    print(f"   ⚠️ Higher priority task after lower priority!")
                elif priority < self.stats['last_priority']:
                    print(f"   ✅ Correct priority order")
            
            self.stats['last_priority'] = priority
            
            # Add to processing order
            self.processing_order.append({
                'task_id': task_id,
                'priority': priority,
                'name': task_name,
                'processed_at': datetime.now().isoformat()
            })
            
            # Simulate processing
            processing_time = self.simulate_task_processing(task, priority)
            
            # Success simulation (95% success rate, higher for critical tasks)
            success_rate = 0.99 if priority >= 8 else 0.95
            
            if random.random() < success_rate:
                # Success
                self.stats['processed'] += 1
                self.stats['priority_counts'][priority] += 1
                self.stats['department_counts'][department] += 1
                self.stats['processing_times'].append(processing_time)
                
                print(f"   ✅ Task completed in {processing_time:.2f}s")
                
                # Special handling for different priorities
                if priority >= 9:
                    print(f"   🚨 Critical task - escalated to management")
                elif priority >= 7:
                    print(f"   📈 High priority - logged for monitoring")
                elif priority <= 1:
                    print(f"   📦 Background task - queued for later cleanup")
                
                # Acknowledge
                channel.basic_ack(delivery_tag=method.delivery_tag)
                
            else:
                # Failure
                self.stats['failed'] += 1
                print(f"   ❌ Task failed - simulated error")
                
                # High priority tasks get retried
                if priority >= 8:
                    print(f"   🔄 Critical task - will be retried")
                    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                else:
                    print(f"   💀 Task rejected")
                    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        
        except json.JSONDecodeError:
            print(f"❌ JSON parse error")
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            print(f"💥 Processing error: {str(e)}")
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        
        finally:
            process_end = time.time()
            total_time = process_end - process_start
            
            # Show processing summary every 5 tasks
            if self.stats['processed'] % 5 == 0 and self.stats['processed'] > 0:
                self.print_progress_summary()
    
    def print_progress_summary(self):
        """İlerleme özetini yazdırır"""
        print(f"\n📊 Progress Summary (Last 5 tasks):")
        if len(self.processing_order) >= 5:
            recent_tasks = self.processing_order[-5:]
            for i, task in enumerate(recent_tasks, 1):
                priority_info = self.get_priority_info(task['priority'])
                print(f"   {i}. {priority_info['emoji']} P{task['priority']}: {task['name'][:30]}...")
    
    def print_final_statistics(self):
        """Final istatistikleri yazdırır"""
        if self.stats['start_time']:
            elapsed = datetime.now() - self.stats['start_time']
            elapsed_seconds = elapsed.total_seconds()
            
            print(f"\n📈 Priority Consumer Final Statistics:")
            print("=" * 50)
            print(f"   ⏱️ Runtime: {elapsed_seconds:.1f}s")
            print(f"   ✅ Processed: {self.stats['processed']}")
            print(f"   ❌ Failed: {self.stats['failed']}")
            
            total_tasks = self.stats['processed'] + self.stats['failed']
            if total_tasks > 0:
                success_rate = (self.stats['processed'] / total_tasks) * 100
                print(f"   📈 Success Rate: {success_rate:.1f}%")
                
                if elapsed_seconds > 0:
                    throughput = total_tasks / elapsed_seconds
                    print(f"   🚀 Throughput: {throughput:.2f} tasks/sec")
            
            # Priority distribution
            if self.stats['priority_counts']:
                print(f"\n🎯 Priority Distribution:")
                for priority in range(10, -1, -1):
                    count = self.stats['priority_counts'][priority]
                    if count > 0:
                        priority_info = self.get_priority_info(priority)
                        percentage = (count / self.stats['processed']) * 100
                        print(f"   {priority_info['emoji']} P{priority} ({priority_info['level']}): {count} ({percentage:.1f}%)")
            
            # Department distribution
            if self.stats['department_counts']:
                print(f"\n🏢 Department Distribution:")
                for dept, count in sorted(self.stats['department_counts'].items()):
                    percentage = (count / self.stats['processed']) * 100
                    print(f"   📋 {dept.title()}: {count} ({percentage:.1f}%)")
            
            # Processing times
            if self.stats['processing_times']:
                avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
                min_time = min(self.stats['processing_times'])
                max_time = max(self.stats['processing_times'])
                print(f"\n⏱️ Processing Times:")
                print(f"   📊 Average: {avg_time:.2f}s")
                print(f"   ⚡ Fastest: {min_time:.2f}s") 
                print(f"   🐌 Slowest: {max_time:.2f}s")
            
            # Processing order analysis
            if len(self.processing_order) > 1:
                print(f"\n📋 Processing Order Analysis:")
                priority_violations = 0
                for i in range(1, len(self.processing_order)):
                    current_priority = self.processing_order[i]['priority']
                    previous_priority = self.processing_order[i-1]['priority']
                    if current_priority > previous_priority:
                        priority_violations += 1
                
                order_compliance = ((len(self.processing_order) - 1 - priority_violations) / (len(self.processing_order) - 1)) * 100
                print(f"   ✅ Priority Order Compliance: {order_compliance:.1f}%")
                print(f"   ⚠️ Priority Violations: {priority_violations}")
                
                if len(self.processing_order) <= 20:
                    print(f"\n📜 Processing Order (last {min(10, len(self.processing_order))} tasks):")
                    for i, task in enumerate(self.processing_order[-10:], 1):
                        priority_info = self.get_priority_info(task['priority'])
                        print(f"   {i:2d}. {priority_info['emoji']} P{task['priority']}: {task['name'][:40]}")
    
    def start_consuming(self):
        """Consumer'ı başlatır"""
        print(f"🎧 Priority Task Consumer başlatılıyor...")
        print(f"📋 Queue: {self.queue_name}")
        print(f"⚡ Fast Mode: {'Enabled' if self.fast_mode else 'Disabled'}")
        print("🛑 Çıkış için Ctrl+C")
        print("=" * 50)
        
        # QoS settings - tek seferde sadece 1 mesaj al
        self.channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.process_task
        )
        
        try:
            while self.running:
                self.connection.process_data_events(time_limit=1)
        except KeyboardInterrupt:
            print(f"\n🛑 KeyboardInterrupt")
        finally:
            print(f"\n🏁 Consumer durduruluyor...")
            self.print_final_statistics()
            self.connection.close()


def main():
    parser = argparse.ArgumentParser(description='RabbitMQ Priority Consumer')
    parser.add_argument('--queue', default='task_queue',
                       choices=['task_queue', 'urgent_tasks', 'background_tasks'],
                       help='Consume edilecek queue')
    parser.add_argument('--fast', action='store_true',
                       help='Hızlı işleme modu (10x faster)')
    
    args = parser.parse_args()
    
    consumer = PriorityConsumer(
        queue_name=args.queue,
        fast_mode=args.fast
    )
    
    consumer.start_consuming()


if __name__ == "__main__":
    main()