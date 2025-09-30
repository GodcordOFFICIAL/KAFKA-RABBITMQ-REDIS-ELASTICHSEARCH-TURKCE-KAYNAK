"""
Comprehensive Monitoring Dashboard
Unified monitoring for Kafka, RabbitMQ, Redis, and Elasticsearch
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Import technology checkers
try:
    from ecommerce_platform import TechnologyChecker, EventBus
except ImportError:
    print("⚠️ ecommerce_platform module not found. Run from integration/python directory.")
    exit(1)

# Technology-specific imports
try:
    import redis
except ImportError:
    redis = None

try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None

try:
    import pika
except ImportError:
    pika = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnologyHealthChecker:
    """Individual technology health checkers"""
    
    @staticmethod
    def check_kafka_health() -> Dict:
        """Check Kafka cluster health"""
        try:
            # This would normally use AdminClient for real health checks
            # For now, simulate basic connectivity
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                request_timeout_ms=5000,
                api_version=(0, 10, 1)
            )
            producer.close()
            
            return {
                'status': 'healthy',
                'brokers': 1,  # Simulated
                'topics': 5,   # Simulated
                'partitions': 15,  # Simulated
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    @staticmethod
    def check_rabbitmq_health() -> Dict:
        """Check RabbitMQ health"""
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost', connection_attempts=3, retry_delay=1)
            )
            channel = connection.channel()
            
            # Get queue info (simplified)
            queues_info = []
            for queue_name in ['email.queue', 'sms.queue', 'push.queue']:
                try:
                    method = channel.queue_declare(queue=queue_name, passive=True)
                    queues_info.append({
                        'name': queue_name,
                        'messages': method.method.message_count,
                        'consumers': method.method.consumer_count
                    })
                except Exception:
                    queues_info.append({
                        'name': queue_name,
                        'messages': 0,
                        'consumers': 0
                    })
            
            connection.close()
            
            return {
                'status': 'healthy',
                'queues': queues_info,
                'total_queues': len(queues_info),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    @staticmethod
    def check_redis_health() -> Dict:
        """Check Redis health"""
        try:
            client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            client.ping()
            
            info = client.info()
            
            return {
                'status': 'healthy',
                'version': info.get('redis_version', 'unknown'),
                'uptime_seconds': info.get('uptime_in_seconds', 0),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'memory_usage_percent': (info.get('used_memory', 0) / info.get('total_system_memory', 1)) * 100,
                'total_commands_processed': info.get('total_commands_processed', 0),
                'ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'hit_rate': TechnologyHealthChecker._calculate_redis_hit_rate(info),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    @staticmethod
    def check_elasticsearch_health() -> Dict:
        """Check Elasticsearch health"""
        try:
            es = Elasticsearch(['localhost:9200'], request_timeout=5)
            
            # Cluster health
            health = es.cluster.health()
            
            # Node info
            nodes = es.cat.nodes(format='json')
            
            # Index info
            indices = es.cat.indices(format='json')
            
            return {
                'status': health['status'],
                'cluster_name': health['cluster_name'],
                'number_of_nodes': health['number_of_nodes'],
                'number_of_data_nodes': health['number_of_data_nodes'],
                'active_shards': health['active_shards'],
                'relocating_shards': health['relocating_shards'],
                'initializing_shards': health['initializing_shards'],
                'unassigned_shards': health['unassigned_shards'],
                'indices_count': len(indices) if indices else 0,
                'total_docs': sum(int(idx.get('docs.count', 0)) for idx in indices if indices),
                'store_size': sum(int(idx.get('store.size', 0)) for idx in indices if indices),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    @staticmethod
    def _calculate_redis_hit_rate(info: Dict) -> float:
        """Calculate Redis cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return (hits / total) * 100

class SystemMetricsCollector:
    """Collect system-wide metrics"""
    
    def __init__(self):
        self.available_tech = TechnologyChecker.get_available_technologies()
    
    def collect_all_metrics(self) -> Dict:
        """Collect metrics from all available technologies"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'collection_duration_ms': 0,
            'technologies': {}
        }
        
        start_time = time.time()
        
        # Kafka metrics
        if self.available_tech['kafka']:
            try:
                metrics['technologies']['kafka'] = TechnologyHealthChecker.check_kafka_health()
            except Exception as e:
                metrics['technologies']['kafka'] = {'status': 'error', 'error': str(e)}
        
        # RabbitMQ metrics
        if self.available_tech['rabbitmq']:
            try:
                metrics['technologies']['rabbitmq'] = TechnologyHealthChecker.check_rabbitmq_health()
            except Exception as e:
                metrics['technologies']['rabbitmq'] = {'status': 'error', 'error': str(e)}
        
        # Redis metrics
        if self.available_tech['redis']:
            try:
                metrics['technologies']['redis'] = TechnologyHealthChecker.check_redis_health()
            except Exception as e:
                metrics['technologies']['redis'] = {'status': 'error', 'error': str(e)}
        
        # Elasticsearch metrics
        if self.available_tech['elasticsearch']:
            try:
                metrics['technologies']['elasticsearch'] = TechnologyHealthChecker.check_elasticsearch_health()
            except Exception as e:
                metrics['technologies']['elasticsearch'] = {'status': 'error', 'error': str(e)}
        
        end_time = time.time()
        metrics['collection_duration_ms'] = int((end_time - start_time) * 1000)
        
        return metrics

class PerformanceAnalyzer:
    """Analyze performance across technologies"""
    
    def __init__(self, metrics_collector: SystemMetricsCollector):
        self.metrics_collector = metrics_collector
        self.historical_metrics = []
    
    def analyze_performance(self, current_metrics: Dict) -> Dict:
        """Analyze current performance and trends"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'healthy',
            'performance_score': 100,
            'alerts': [],
            'recommendations': [],
            'technology_scores': {}
        }
        
        for tech_name, tech_metrics in current_metrics['technologies'].items():
            score = self._calculate_technology_score(tech_name, tech_metrics)
            analysis['technology_scores'][tech_name] = score
            
            # Generate alerts and recommendations
            alerts, recommendations = self._analyze_technology_health(tech_name, tech_metrics)
            analysis['alerts'].extend(alerts)
            analysis['recommendations'].extend(recommendations)
            
            # Update overall health
            if tech_metrics.get('status') == 'unhealthy':
                analysis['overall_health'] = 'degraded'
        
        # Calculate overall performance score
        if analysis['technology_scores']:
            analysis['performance_score'] = sum(analysis['technology_scores'].values()) / len(analysis['technology_scores'])
        
        return analysis
    
    def _calculate_technology_score(self, tech_name: str, metrics: Dict) -> int:
        """Calculate performance score for a technology (0-100)"""
        if metrics.get('status') == 'unhealthy':
            return 0
        
        if tech_name == 'redis':
            # Redis scoring based on memory usage and hit rate
            memory_usage = metrics.get('memory_usage_percent', 0)
            hit_rate = metrics.get('hit_rate', 100)
            
            memory_score = max(0, 100 - memory_usage) if memory_usage < 80 else 50
            hit_rate_score = hit_rate
            
            return int((memory_score + hit_rate_score) / 2)
        
        elif tech_name == 'elasticsearch':
            # Elasticsearch scoring based on cluster status
            status = metrics.get('status', 'red')
            unassigned_shards = metrics.get('unassigned_shards', 0)
            
            if status == 'green' and unassigned_shards == 0:
                return 100
            elif status == 'yellow':
                return 75
            else:
                return 50
        
        elif tech_name == 'kafka':
            # Kafka scoring (simplified)
            return 90 if metrics.get('status') == 'healthy' else 50
        
        elif tech_name == 'rabbitmq':
            # RabbitMQ scoring (simplified)
            return 90 if metrics.get('status') == 'healthy' else 50
        
        return 80  # Default score
    
    def _analyze_technology_health(self, tech_name: str, metrics: Dict) -> tuple:
        """Analyze individual technology health and generate alerts/recommendations"""
        alerts = []
        recommendations = []
        
        if tech_name == 'redis':
            memory_usage = metrics.get('memory_usage_percent', 0)
            hit_rate = metrics.get('hit_rate', 100)
            
            if memory_usage > 90:
                alerts.append({
                    'level': 'critical',
                    'technology': 'redis',
                    'message': f'Redis memory usage critical: {memory_usage:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
                recommendations.append({
                    'technology': 'redis',
                    'priority': 'high',
                    'action': 'Increase Redis memory or implement data eviction policies',
                    'details': f'Current usage: {memory_usage:.1f}%'
                })
            
            if hit_rate < 80:
                alerts.append({
                    'level': 'warning',
                    'technology': 'redis',
                    'message': f'Redis hit rate low: {hit_rate:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
                recommendations.append({
                    'technology': 'redis',
                    'priority': 'medium',
                    'action': 'Review caching strategy and TTL settings',
                    'details': f'Current hit rate: {hit_rate:.1f}%'
                })
        
        elif tech_name == 'elasticsearch':
            status = metrics.get('status', 'red')
            unassigned_shards = metrics.get('unassigned_shards', 0)
            
            if status == 'red':
                alerts.append({
                    'level': 'critical',
                    'technology': 'elasticsearch',
                    'message': 'Elasticsearch cluster status is RED',
                    'timestamp': datetime.now().isoformat()
                })
                recommendations.append({
                    'technology': 'elasticsearch',
                    'priority': 'critical',
                    'action': 'Investigate cluster issues immediately',
                    'details': 'RED status indicates data loss or unavailability'
                })
            
            if unassigned_shards > 0:
                alerts.append({
                    'level': 'warning',
                    'technology': 'elasticsearch',
                    'message': f'{unassigned_shards} unassigned shards detected',
                    'timestamp': datetime.now().isoformat()
                })
        
        elif tech_name == 'rabbitmq':
            if metrics.get('status') == 'unhealthy':
                alerts.append({
                    'level': 'critical',
                    'technology': 'rabbitmq',
                    'message': 'RabbitMQ connection failed',
                    'timestamp': datetime.now().isoformat()
                })
        
        elif tech_name == 'kafka':
            if metrics.get('status') == 'unhealthy':
                alerts.append({
                    'level': 'critical',
                    'technology': 'kafka',
                    'message': 'Kafka cluster unreachable',
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts, recommendations

class MonitoringDashboard:
    """Comprehensive monitoring dashboard"""
    
    def __init__(self):
        self.metrics_collector = SystemMetricsCollector()
        self.performance_analyzer = PerformanceAnalyzer(self.metrics_collector)
        self.available_tech = TechnologyChecker.get_available_technologies()
    
    def display_dashboard(self, refresh_interval: int = 30, max_iterations: int = 3):
        """Display real-time monitoring dashboard"""
        print("📊 Integrated Technology Monitoring Dashboard")
        print("=" * 80)
        
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                
                # Clear screen (simplified)
                if iteration > 1:
                    print("\n" + "="*80)
                    print(f"📊 Dashboard Refresh #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                    print("=" * 80)
                
                # Collect current metrics
                current_metrics = self.metrics_collector.collect_all_metrics()
                
                # Analyze performance
                analysis = self.performance_analyzer.analyze_performance(current_metrics)
                
                # Display overview
                self._display_overview(current_metrics, analysis)
                
                # Display technology details
                self._display_technology_details(current_metrics)
                
                # Display alerts and recommendations
                self._display_alerts_and_recommendations(analysis)
                
                # Display system summary
                self._display_system_summary(current_metrics, analysis)
                
                if iteration < max_iterations:
                    print(f"\n⏳ Next refresh in {refresh_interval} seconds... (Ctrl+C to stop)")
                    time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring dashboard stopped by user")
    
    def _display_overview(self, metrics: Dict, analysis: Dict):
        """Display high-level overview"""
        overall_health = analysis['overall_health']
        performance_score = analysis['performance_score']
        
        health_emoji = "🟢" if overall_health == 'healthy' else "🟡"
        score_emoji = "🟢" if performance_score >= 80 else "🟡" if performance_score >= 60 else "🔴"
        
        print(f"\n{health_emoji} Overall Health: {overall_health.upper()}")
        print(f"{score_emoji} Performance Score: {performance_score:.1f}/100")
        print(f"📅 Last Updated: {metrics['timestamp']}")
        print(f"⚡ Collection Time: {metrics['collection_duration_ms']}ms")
    
    def _display_technology_details(self, metrics: Dict):
        """Display detailed technology metrics"""
        print(f"\n🔧 Technology Status:")
        
        for tech_name, tech_metrics in metrics['technologies'].items():
            status = tech_metrics.get('status', 'unknown')
            status_emoji = "✅" if status == 'healthy' else "🟡" if status == 'yellow' else "❌"
            
            print(f"\n   {status_emoji} {tech_name.upper()}: {status}")
            
            if 'error' in tech_metrics:
                print(f"      Error: {tech_metrics['error']}")
                continue
            
            # Technology-specific details
            if tech_name == 'redis':
                print(f"      Memory: {tech_metrics.get('used_memory', 'N/A')}")
                print(f"      Clients: {tech_metrics.get('connected_clients', 0)}")
                print(f"      Ops/sec: {tech_metrics.get('ops_per_sec', 0)}")
                print(f"      Hit Rate: {tech_metrics.get('hit_rate', 0):.1f}%")
            
            elif tech_name == 'elasticsearch':
                print(f"      Nodes: {tech_metrics.get('number_of_nodes', 0)}")
                print(f"      Active Shards: {tech_metrics.get('active_shards', 0)}")
                print(f"      Indices: {tech_metrics.get('indices_count', 0)}")
                unassigned = tech_metrics.get('unassigned_shards', 0)
                if unassigned > 0:
                    print(f"      ⚠️ Unassigned Shards: {unassigned}")
            
            elif tech_name == 'rabbitmq':
                queues = tech_metrics.get('queues', [])
                print(f"      Total Queues: {len(queues)}")
                for queue in queues:
                    if queue['messages'] > 0:
                        print(f"        📬 {queue['name']}: {queue['messages']} messages")
            
            elif tech_name == 'kafka':
                print(f"      Brokers: {tech_metrics.get('brokers', 0)}")
                print(f"      Topics: {tech_metrics.get('topics', 0)}")
                print(f"      Partitions: {tech_metrics.get('partitions', 0)}")
    
    def _display_alerts_and_recommendations(self, analysis: Dict):
        """Display alerts and recommendations"""
        alerts = analysis.get('alerts', [])
        recommendations = analysis.get('recommendations', [])
        
        if alerts:
            print(f"\n🚨 Active Alerts ({len(alerts)}):")
            for alert in alerts:
                level_emoji = "🔴" if alert['level'] == 'critical' else "🟡"
                print(f"   {level_emoji} {alert['technology'].upper()}: {alert['message']}")
        
        if recommendations:
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for rec in recommendations:
                priority_emoji = "🔴" if rec['priority'] == 'critical' else "🟡" if rec['priority'] == 'high' else "🟢"
                print(f"   {priority_emoji} {rec['technology'].upper()}: {rec['action']}")
                if 'details' in rec:
                    print(f"      Details: {rec['details']}")
    
    def _display_system_summary(self, metrics: Dict, analysis: Dict):
        """Display system summary"""
        available_count = len(metrics['technologies'])
        healthy_count = sum(1 for tech in metrics['technologies'].values() 
                          if tech.get('status') in ['healthy', 'green', 'yellow'])
        
        print(f"\n📊 System Summary:")
        print(f"   Technologies Available: {available_count}/4")
        print(f"   Healthy Services: {healthy_count}/{available_count}")
        print(f"   Active Alerts: {len(analysis.get('alerts', []))}")
        print(f"   Recommendations: {len(analysis.get('recommendations', []))}")
        
        # Technology scores
        tech_scores = analysis.get('technology_scores', {})
        if tech_scores:
            print(f"   Technology Scores:")
            for tech, score in tech_scores.items():
                score_emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                print(f"     {score_emoji} {tech.upper()}: {score}/100")

def demo_monitoring_dashboard():
    """
    Monitoring dashboard demo
    """
    print("📊 Integrated Monitoring Dashboard Demo")
    print("=" * 60)
    
    # Check available technologies
    available_tech = TechnologyChecker.get_available_technologies()
    
    print("\n🔍 Technology Availability Check:")
    for tech, available in available_tech.items():
        status = "✅" if available else "❌"
        print(f"   {status} {tech.upper()}: {'Available' if available else 'Not available'}")
    
    if not any(available_tech.values()):
        print("\n⚠️ No technologies available for monitoring.")
        print("\n💡 To start services:")
        print("   • Kafka: make start-kafka")
        print("   • RabbitMQ: make start-rabbitmq")
        print("   • Redis: make start-redis")
        print("   • Elasticsearch: make start-elasticsearch")
        return
    
    # Initialize and run dashboard
    dashboard = MonitoringDashboard()
    
    print(f"\n🚀 Starting monitoring dashboard...")
    print(f"   Monitoring {sum(available_tech.values())} technologies")
    print(f"   Dashboard will refresh every 30 seconds")
    
    # Run dashboard with limited iterations for demo
    dashboard.display_dashboard(refresh_interval=10, max_iterations=2)
    
    print("\n✅ Monitoring dashboard demo completed!")
    print("\n🎯 This demo showcased:")
    print("   • Real-time health monitoring for all technologies")
    print("   • Performance scoring and analysis")
    print("   • Automated alert generation")
    print("   • Actionable recommendations")
    print("   • Comprehensive system overview")

if __name__ == "__main__":
    demo_monitoring_dashboard()