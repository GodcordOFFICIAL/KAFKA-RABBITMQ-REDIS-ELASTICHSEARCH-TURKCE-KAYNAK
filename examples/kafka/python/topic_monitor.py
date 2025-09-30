# examples/kafka/python/topic_monitor.py
"""
Kafka Topic Monitoring ve Health Check Utility

Bu script Kafka topic'lerinin sağlık durumunu izlemek ve 
performans metriklerini takip etmek için kullanılır.

Özellikler:
- Topic listesi ve detayları
- Health check ve problem detection
- Performance metrics
- Retention policy analizi
- Under-replicated partition detection
"""

import json
import subprocess
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import re

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TopicInfo:
    """Topic bilgilerini saklayan data class"""
    name: str
    partition_count: int = 0
    replication_factor: int = 0
    partitions: List[Dict] = None
    configs: Dict[str, str] = None
    
    def __post_init__(self):
        if self.partitions is None:
            self.partitions = []
        if self.configs is None:
            self.configs = {}

class TopicMonitor:
    """
    Kafka Topic Monitoring ve Health Check Utility
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092", 
                 kafka_container: str = "kafka1"):
        """
        TopicMonitor initialization
        
        Args:
            bootstrap_servers: Kafka broker addresses
            kafka_container: Docker container name for Kafka
        """
        self.bootstrap_servers = bootstrap_servers
        self.kafka_container = kafka_container
        
        # Health check thresholds
        self.thresholds = {
            'min_replication_factor': 3,
            'max_retention_days': 30,
            'max_partition_count': 100,
            'min_partition_count': 1
        }
        
        logger.info(f"✅ TopicMonitor initialized for {bootstrap_servers}")
    
    def _run_kafka_command(self, command: List[str]) -> Optional[str]:
        """
        Kafka CLI komutlarını çalıştırır
        
        Args:
            command: Kafka CLI command list
            
        Returns:
            Command output or None if failed
        """
        try:
            full_command = ["docker", "exec", "-it", self.kafka_container] + command
            result = subprocess.run(
                full_command, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"❌ Command failed: {' '.join(command)}")
                logger.error(f"Error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Command timeout: {' '.join(command)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error running command: {e}")
            return None
    
    def is_kafka_accessible(self) -> bool:
        """
        Kafka cluster'ın erişilebilir olup olmadığını kontrol eder
        
        Returns:
            True if accessible, False otherwise
        """
        command = [
            "kafka-broker-api-versions.sh",
            "--bootstrap-server", self.bootstrap_servers
        ]
        
        result = self._run_kafka_command(command)
        return result is not None
    
    def get_topic_list(self, include_internal: bool = False) -> List[str]:
        """
        Tüm topic'leri listeler
        
        Args:
            include_internal: Include internal topics (starting with _)
            
        Returns:
            List of topic names
        """
        command = [
            "kafka-topics.sh",
            "--list",
            "--bootstrap-server", self.bootstrap_servers
        ]
        
        result = self._run_kafka_command(command)
        if not result:
            return []
        
        topics = [topic.strip() for topic in result.split('\n') if topic.strip()]
        
        if not include_internal:
            topics = [topic for topic in topics if not topic.startswith('_')]
        
        return sorted(topics)
    
    def get_topic_details(self, topic: str) -> Optional[TopicInfo]:
        """
        Topic detaylarını alır
        
        Args:
            topic: Topic name
            
        Returns:
            TopicInfo object or None if failed
        """
        command = [
            "kafka-topics.sh",
            "--describe",
            "--bootstrap-server", self.bootstrap_servers,
            "--topic", topic
        ]
        
        result = self._run_kafka_command(command)
        if not result:
            return None
        
        topic_info = TopicInfo(name=topic)
        lines = result.split('\n')
        
        # Parse topic summary line
        summary_line = lines[0] if lines else ""
        if f"Topic: {topic}" in summary_line:
            # Extract partition count and replication factor
            partition_match = re.search(r'PartitionCount: (\d+)', summary_line)
            replication_match = re.search(r'ReplicationFactor: (\d+)', summary_line)
            
            if partition_match:
                topic_info.partition_count = int(partition_match.group(1))
            if replication_match:
                topic_info.replication_factor = int(replication_match.group(1))
        
        # Parse partition details
        for line in lines[1:]:
            if line.strip().startswith("Partition:"):
                partition_info = self._parse_partition_line(line)
                if partition_info:
                    topic_info.partitions.append(partition_info)
        
        # Get topic configurations
        topic_info.configs = self.get_topic_configs(topic)
        
        return topic_info
    
    def _parse_partition_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Partition line'ını parse eder
        
        Args:
            line: Partition description line
            
        Returns:
            Partition info dictionary
        """
        try:
            partition_info = {}
            
            # Extract partition ID
            partition_match = re.search(r'Partition: (\d+)', line)
            if partition_match:
                partition_info['id'] = int(partition_match.group(1))
            
            # Extract leader
            leader_match = re.search(r'Leader: (\d+|-?\w+)', line)
            if leader_match:
                leader_str = leader_match.group(1)
                partition_info['leader'] = int(leader_str) if leader_str.isdigit() else leader_str
            
            # Extract replicas
            replicas_match = re.search(r'Replicas: ([\d,]+)', line)
            if replicas_match:
                replicas_str = replicas_match.group(1)
                partition_info['replicas'] = [int(r) for r in replicas_str.split(',')]
            
            # Extract ISR
            isr_match = re.search(r'Isr: ([\d,]*)', line)
            if isr_match:
                isr_str = isr_match.group(1)
                partition_info['isr'] = [int(r) for r in isr_str.split(',') if r]
            
            return partition_info if partition_info else None
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing partition line: {e}")
            return None
    
    def get_topic_configs(self, topic: str) -> Dict[str, str]:
        """
        Topic configuration'larını alır
        
        Args:
            topic: Topic name
            
        Returns:
            Configuration dictionary
        """
        command = [
            "kafka-configs.sh",
            "--bootstrap-server", self.bootstrap_servers,
            "--entity-type", "topics",
            "--entity-name", topic,
            "--describe"
        ]
        
        result = self._run_kafka_command(command)
        if not result:
            return {}
        
        configs = {}
        lines = result.split('\n')
        
        for line in lines:
            # Skip header lines
            if 'Dynamic configs' in line or not line.strip():
                continue
            
            # Parse key=value pairs
            if '=' in line:
                try:
                    # Handle multiple configs in one line
                    config_parts = line.strip().split(' ')
                    for part in config_parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            configs[key.strip()] = value.strip()
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing config line: {line}")
        
        return configs
    
    def check_topic_health(self, topic: str) -> Dict[str, Any]:
        """
        Topic health check yapar
        
        Args:
            topic: Topic name
            
        Returns:
            Health check results
        """
        health = {
            "topic": topic,
            "healthy": True,
            "issues": [],
            "warnings": [],
            "recommendations": [],
            "score": 100
        }
        
        try:
            # Get topic details
            topic_info = self.get_topic_details(topic)
            if not topic_info:
                health["healthy"] = False
                health["issues"].append("Topic details could not be retrieved")
                health["score"] = 0
                return health
            
            # Check replication factor
            if topic_info.replication_factor < self.thresholds['min_replication_factor']:
                if topic_info.replication_factor == 1:
                    health["issues"].append(f"No replication (RF=1) - data loss risk")
                    health["score"] -= 30
                else:
                    health["warnings"].append(f"Low replication factor: {topic_info.replication_factor}")
                    health["score"] -= 15
                health["recommendations"].append(
                    f"Increase replication factor to {self.thresholds['min_replication_factor']} for production"
                )
            
            # Check partition count
            if topic_info.partition_count == 1:
                health["warnings"].append("Single partition - limited parallelism")
                health["recommendations"].append("Consider increasing partition count for better throughput")
                health["score"] -= 10
            elif topic_info.partition_count > self.thresholds['max_partition_count']:
                health["warnings"].append(f"High partition count: {topic_info.partition_count}")
                health["recommendations"].append("Consider reducing partition count to avoid metadata overhead")
                health["score"] -= 5
            
            # Check for under-replicated partitions
            under_replicated = []
            leader_issues = []
            
            for partition in topic_info.partitions:
                replicas = partition.get('replicas', [])
                isr = partition.get('isr', [])
                leader = partition.get('leader')
                
                # Check under-replication
                if len(isr) < len(replicas):
                    under_replicated.append(partition['id'])
                
                # Check leader issues
                if leader == 'none' or leader == -1:
                    leader_issues.append(partition['id'])
            
            if under_replicated:
                health["healthy"] = False
                health["issues"].append(f"Under-replicated partitions: {under_replicated}")
                health["recommendations"].append("Check broker health and network connectivity")
                health["score"] -= 40
            
            if leader_issues:
                health["healthy"] = False
                health["issues"].append(f"Partitions without leader: {leader_issues}")
                health["recommendations"].append("Check broker availability and leader election")
                health["score"] -= 50
            
            # Check retention settings
            retention_ms = topic_info.configs.get('retention.ms')
            if retention_ms:
                try:
                    retention_days = int(retention_ms) / (1000 * 60 * 60 * 24)
                    if retention_days > self.thresholds['max_retention_days']:
                        health["warnings"].append(f"Long retention period: {retention_days:.1f} days")
                        health["recommendations"].append("Consider reducing retention period to save storage")
                        health["score"] -= 5
                except ValueError:
                    pass
            
            # Check cleanup policy
            cleanup_policy = topic_info.configs.get('cleanup.policy', 'delete')
            if cleanup_policy not in ['delete', 'compact', 'compact,delete']:
                health["warnings"].append(f"Unusual cleanup policy: {cleanup_policy}")
                health["score"] -= 5
            
            # Check compression
            compression = topic_info.configs.get('compression.type', 'producer')
            if compression == 'uncompressed':
                health["warnings"].append("No compression - higher storage/network usage")
                health["recommendations"].append("Consider enabling compression (gzip/lz4)")
                health["score"] -= 5
            
            # Final health determination
            if health["score"] >= 80:
                health["healthy"] = True
            elif health["score"] >= 60:
                health["healthy"] = len(health["issues"]) == 0
            else:
                health["healthy"] = False
            
            # Add summary
            health["summary"] = {
                "partition_count": topic_info.partition_count,
                "replication_factor": topic_info.replication_factor,
                "under_replicated_partitions": len(under_replicated),
                "retention_policy": cleanup_policy,
                "compression": compression
            }
            
            return health
            
        except Exception as e:
            health["healthy"] = False
            health["issues"].append(f"Health check failed: {e}")
            health["score"] = 0
            return health
    
    def generate_health_report(self, topics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Topic'ler için health report oluşturur
        
        Args:
            topics: Specific topics to check (None for all)
            
        Returns:
            Health report dictionary
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "cluster": self.bootstrap_servers,
            "topics": {},
            "summary": {
                "total_topics": 0,
                "healthy_topics": 0,
                "topics_with_warnings": 0,
                "topics_with_issues": 0,
                "critical_issues": 0,
                "average_score": 0
            }
        }
        
        if topics is None:
            topics = self.get_topic_list()
        
        total_score = 0
        
        for topic in topics:
            if topic.startswith('_'):  # Skip internal topics
                continue
            
            health = self.check_topic_health(topic)
            report["topics"][topic] = health
            
            report["summary"]["total_topics"] += 1
            total_score += health["score"]
            
            if health["healthy"]:
                report["summary"]["healthy_topics"] += 1
            
            if health["warnings"]:
                report["summary"]["topics_with_warnings"] += 1
            
            if health["issues"]:
                report["summary"]["topics_with_issues"] += 1
                
                # Count critical issues
                critical_keywords = [
                    "Under-replicated", "could not be retrieved", 
                    "without leader", "No replication"
                ]
                for issue in health["issues"]:
                    if any(keyword in issue for keyword in critical_keywords):
                        report["summary"]["critical_issues"] += 1
                        break
        
        # Calculate average score
        if report["summary"]["total_topics"] > 0:
            report["summary"]["average_score"] = total_score / report["summary"]["total_topics"]
        
        return report
    
    def print_health_report(self, topics: Optional[List[str]] = None, 
                          detailed: bool = False):
        """
        Health report'u console'a yazdırır
        
        Args:
            topics: Specific topics to check
            detailed: Show detailed information
        """
        # Check Kafka connectivity first
        if not self.is_kafka_accessible():
            logger.error("❌ Cannot connect to Kafka cluster")
            return
        
        report = self.generate_health_report(topics)
        
        print("📊 Kafka Topic Health Report")
        print("=" * 60)
        print(f"🕐 Timestamp: {report['timestamp']}")
        print(f"🌐 Cluster: {report['cluster']}")
        print(f"📁 Total Topics: {report['summary']['total_topics']}")
        print(f"✅ Healthy Topics: {report['summary']['healthy_topics']}")
        print(f"⚠️ Topics with Warnings: {report['summary']['topics_with_warnings']}")
        print(f"❌ Topics with Issues: {report['summary']['topics_with_issues']}")
        print(f"🚨 Critical Issues: {report['summary']['critical_issues']}")
        print(f"📊 Average Score: {report['summary']['average_score']:.1f}/100")
        print()
        
        # Overall cluster health
        avg_score = report['summary']['average_score']
        if avg_score >= 90:
            print("🎉 Cluster Health: EXCELLENT")
        elif avg_score >= 80:
            print("✅ Cluster Health: GOOD")
        elif avg_score >= 70:
            print("⚠️ Cluster Health: FAIR")
        elif avg_score >= 60:
            print("🔶 Cluster Health: POOR")
        else:
            print("🚨 Cluster Health: CRITICAL")
        print()
        
        # Topic details
        for topic_name, health in report["topics"].items():
            score = health["score"]
            if score >= 90:
                status_icon = "🎯"
            elif score >= 80:
                status_icon = "✅"
            elif score >= 70:
                status_icon = "⚠️"
            elif score >= 60:
                status_icon = "🔶"
            else:
                status_icon = "🚨"
            
            print(f"{status_icon} Topic: {topic_name} (Score: {score}/100)")
            
            if health.get("summary") and detailed:
                summary = health["summary"]
                print(f"   📊 Partitions: {summary['partition_count']}")
                print(f"   🔄 Replication Factor: {summary['replication_factor']}")
                print(f"   🗑️ Cleanup Policy: {summary['retention_policy']}")
                print(f"   📦 Compression: {summary['compression']}")
            
            if health["issues"]:
                print(f"   🚨 Issues:")
                for issue in health["issues"]:
                    print(f"      - {issue}")
            
            if health["warnings"] and detailed:
                print(f"   ⚠️ Warnings:")
                for warning in health["warnings"]:
                    print(f"      - {warning}")
            
            if health["recommendations"] and detailed:
                print(f"   💡 Recommendations:")
                for rec in health["recommendations"]:
                    print(f"      - {rec}")
            
            print()
    
    def monitor_continuously(self, interval: int = 60, topics: Optional[List[str]] = None):
        """
        Continuous monitoring
        
        Args:
            interval: Check interval in seconds
            topics: Specific topics to monitor
        """
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        
        try:
            while True:
                print("\n" + "="*80)
                print(f"🔄 Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*80)
                
                self.print_health_report(topics, detailed=False)
                
                print(f"⏰ Next check in {interval} seconds... (Ctrl+C to stop)")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("⚠️ Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")

# CLI interface
def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Kafka Topic Health Monitor')
    parser.add_argument('--bootstrap-servers', default='localhost:9092',
                       help='Kafka bootstrap servers')
    parser.add_argument('--container', default='kafka1',
                       help='Kafka docker container name')
    parser.add_argument('--topics', nargs='*',
                       help='Specific topics to monitor')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed information')
    parser.add_argument('--monitor', action='store_true',
                       help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=60,
                       help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    monitor = TopicMonitor(args.bootstrap_servers, args.container)
    
    if args.monitor:
        monitor.monitor_continuously(args.interval, args.topics)
    else:
        monitor.print_health_report(args.topics, args.detailed)

# Test usage
if __name__ == "__main__":
    main()