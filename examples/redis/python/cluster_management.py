"""
Redis Cluster Management ve Production Examples
High availability, automatic failover ve distributed operations
"""

import redis
from rediscluster import RedisCluster
import time
import random
import json
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import hashlib
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisClusterClient:
    """
    Production-ready Redis Cluster client
    """
    
    def __init__(self, startup_nodes=None, **kwargs):
        """
        Initialize Redis Cluster client with production settings
        """
        if startup_nodes is None:
            startup_nodes = [
                {"host": "localhost", "port": "7001"},
                {"host": "localhost", "port": "7002"},
                {"host": "localhost", "port": "7003"},
                {"host": "localhost", "port": "7004"},
                {"host": "localhost", "port": "7005"},
                {"host": "localhost", "port": "7006"}
            ]
        
        # Production cluster configuration
        cluster_config = {
            'startup_nodes': startup_nodes,
            'decode_responses': True,
            'skip_full_coverage_check': True,
            'health_check_interval': 30,
            'max_connections': 32,
            'retry_on_timeout': True,
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            **kwargs
        }
        
        try:
            self.cluster = RedisCluster(**cluster_config)
            self.cluster.ping()
            logger.info(f"✅ Redis Cluster connected - {len(startup_nodes)} nodes")
        except Exception as e:
            logger.error(f"❌ Cluster connection failed: {e}")
            self.cluster = None
    
    def get_cluster_health(self) -> Dict:
        """
        Comprehensive cluster health check
        """
        if not self.cluster:
            return {"status": "disconnected", "error": "No cluster connection"}
        
        try:
            # Basic cluster info
            nodes_info = self.cluster.cluster_nodes()
            
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "total_nodes": len(nodes_info),
                "master_nodes": 0,
                "slave_nodes": 0,
                "failed_nodes": 0,
                "nodes_detail": [],
                "slots_coverage": {"covered": 0, "total": 16384},
                "memory_usage": {},
                "performance_metrics": {}
            }
            
            total_memory_used = 0
            total_memory_max = 0
            
            for node_id, node_info in nodes_info.items():
                node_detail = {
                    "id": node_id[:8],
                    "address": f"{node_info['ip']}:{node_info['port']}",
                    "role": "master" if "master" in node_info.get('flags', []) else "slave",
                    "status": "connected" if "connected" in node_info.get('flags', []) else "failed",
                    "slots": len(node_info.get('slots', [])),
                    "memory_used": 0,
                    "memory_max": 0
                }
                
                # Node durumunu say
                if node_detail["role"] == "master":
                    health_status["master_nodes"] += 1
                else:
                    health_status["slave_nodes"] += 1
                
                if node_detail["status"] == "failed":
                    health_status["failed_nodes"] += 1
                    health_status["status"] = "degraded"
                
                # Slots coverage hesapla
                for slot_range in node_info.get('slots', []):
                    if len(slot_range) == 2:
                        health_status["slots_coverage"]["covered"] += slot_range[1] - slot_range[0] + 1
                
                # Memory bilgilerini al (her node için ayrı connection gerekebilir)
                try:
                    node_client = redis.Redis(host=node_info['ip'], port=node_info['port'], decode_responses=True)
                    memory_info = node_client.info('memory')
                    node_detail["memory_used"] = memory_info.get('used_memory', 0)
                    node_detail["memory_max"] = memory_info.get('maxmemory', 0)
                    
                    total_memory_used += node_detail["memory_used"]
                    total_memory_max += node_detail["memory_max"]
                    
                except Exception as e:
                    logger.warning(f"Could not get memory info for node {node_id}: {e}")
                
                health_status["nodes_detail"].append(node_detail)
            
            # Overall memory usage
            if total_memory_max > 0:
                health_status["memory_usage"] = {
                    "total_used": total_memory_used,
                    "total_max": total_memory_max,
                    "usage_percentage": (total_memory_used / total_memory_max) * 100
                }
            
            # Slots coverage check
            if health_status["slots_coverage"]["covered"] < 16384:
                health_status["status"] = "degraded"
                health_status["warning"] = f"Only {health_status['slots_coverage']['covered']}/16384 slots covered"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}

class DistributedCache:
    """
    High-performance distributed cache using Redis Cluster
    """
    
    def __init__(self, cluster_client: RedisClusterClient, default_ttl: int = 3600):
        self.cluster = cluster_client.cluster
        self.default_ttl = default_ttl
        
    def set_with_hash_tag(self, key: str, value: Any, ttl: Optional[int] = None, hash_tag: str = None) -> bool:
        """
        Set value with optional hash tag for same-slot placement
        """
        if hash_tag:
            # Hash tag'li key oluştur - aynı slot'a gitmesini garanti eder
            tagged_key = f"{{{hash_tag}}}:{key}"
        else:
            tagged_key = key
        
        try:
            ttl = ttl or self.default_ttl
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = self.cluster.setex(tagged_key, ttl, value)
            return result
        except Exception as e:
            logger.error(f"Cache set error for {tagged_key}: {e}")
            return False
    
    def get_with_hash_tag(self, key: str, hash_tag: str = None) -> Any:
        """
        Get value with optional hash tag
        """
        if hash_tag:
            tagged_key = f"{{{hash_tag}}}:{key}"
        else:
            tagged_key = key
        
        try:
            value = self.cluster.get(tagged_key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Cache get error for {tagged_key}: {e}")
            return None
    
    def cache_user_session(self, user_id: int, session_data: Dict, ttl: int = 1800) -> bool:
        """
        Cache user session with consistent hashing
        """
        hash_tag = f"user:{user_id}"
        session_key = f"session:{session_data['session_id']}"
        
        # Session data'sını cache'le
        success = self.set_with_hash_tag(session_key, session_data, ttl, hash_tag)
        
        # User'ın aktif session'larını track et
        if success:
            user_sessions_key = f"user_sessions"
            try:
                self.cluster.sadd(f"{{{hash_tag}}}:{user_sessions_key}", session_data['session_id'])
                self.cluster.expire(f"{{{hash_tag}}}:{user_sessions_key}", ttl)
            except Exception as e:
                logger.error(f"Error tracking user sessions: {e}")
        
        return success
    
    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """
        Get all active sessions for a user
        """
        hash_tag = f"user:{user_id}"
        user_sessions_key = f"{{{hash_tag}}}:user_sessions"
        
        try:
            session_ids = self.cluster.smembers(user_sessions_key)
            sessions = []
            
            for session_id in session_ids:
                session_key = f"session:{session_id}"
                session_data = self.get_with_hash_tag(session_key, hash_tag)
                if session_data:
                    sessions.append(session_data)
            
            return sessions
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def cache_invalidation_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern
        """
        try:
            # Pattern'e uyan key'leri bul
            keys = []
            for key in self.cluster.scan_iter(match=pattern):
                keys.append(key)
            
            # Batch delete
            if keys:
                deleted_count = self.cluster.delete(*keys)
                logger.info(f"Invalidated {deleted_count} cache entries matching {pattern}")
                return deleted_count
            
            return 0
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

class DistributedLock:
    """
    Distributed lock implementation using Redis Cluster
    """
    
    def __init__(self, cluster_client: RedisClusterClient):
        self.cluster = cluster_client.cluster
    
    def acquire_lock(self, lock_name: str, timeout: int = 30, identifier: str = None) -> Optional[str]:
        """
        Acquire distributed lock with timeout
        """
        if not identifier:
            identifier = f"{threading.current_thread().ident}_{int(time.time() * 1000)}"
        
        lock_key = f"lock:{lock_name}"
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                # SET NX EX - atomic operation
                if self.cluster.set(lock_key, identifier, nx=True, ex=timeout):
                    logger.info(f"Lock acquired: {lock_name} by {identifier}")
                    return identifier
                
                # Lock alınamadı, kısa süre bekle
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Lock acquisition error: {e}")
                break
        
        logger.warning(f"Failed to acquire lock: {lock_name}")
        return None
    
    def release_lock(self, lock_name: str, identifier: str) -> bool:
        """
        Release distributed lock with identifier verification
        """
        lock_key = f"lock:{lock_name}"
        
        # Lua script for atomic release
        lua_script = """
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        else
            return 0
        end
        """
        
        try:
            result = self.cluster.eval(lua_script, 1, lock_key, identifier)
            if result:
                logger.info(f"Lock released: {lock_name} by {identifier}")
                return True
            else:
                logger.warning(f"Lock release failed - wrong identifier: {lock_name}")
                return False
        except Exception as e:
            logger.error(f"Lock release error: {e}")
            return False
    
    def with_lock(self, lock_name: str, timeout: int = 30):
        """
        Context manager for distributed lock
        """
        class LockContext:
            def __init__(self, lock_manager, lock_name, timeout):
                self.lock_manager = lock_manager
                self.lock_name = lock_name
                self.timeout = timeout
                self.identifier = None
            
            def __enter__(self):
                self.identifier = self.lock_manager.acquire_lock(self.lock_name, self.timeout)
                if not self.identifier:
                    raise Exception(f"Could not acquire lock: {self.lock_name}")
                return self.identifier
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.identifier:
                    self.lock_manager.release_lock(self.lock_name, self.identifier)
        
        return LockContext(self, lock_name, timeout)

class DistributedCounter:
    """
    High-performance distributed counter with Redis Cluster
    """
    
    def __init__(self, cluster_client: RedisClusterClient):
        self.cluster = cluster_client.cluster
    
    def increment(self, counter_name: str, amount: int = 1) -> int:
        """
        Atomic counter increment
        """
        try:
            current_value = self.cluster.incrby(f"counter:{counter_name}", amount)
            return current_value
        except Exception as e:
            logger.error(f"Counter increment error: {e}")
            return 0
    
    def decrement(self, counter_name: str, amount: int = 1) -> int:
        """
        Atomic counter decrement
        """
        try:
            current_value = self.cluster.decrby(f"counter:{counter_name}", amount)
            return current_value
        except Exception as e:
            logger.error(f"Counter decrement error: {e}")
            return 0
    
    def get_value(self, counter_name: str) -> int:
        """
        Get current counter value
        """
        try:
            value = self.cluster.get(f"counter:{counter_name}")
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Counter get error: {e}")
            return 0
    
    def reset(self, counter_name: str) -> bool:
        """
        Reset counter to zero
        """
        try:
            self.cluster.delete(f"counter:{counter_name}")
            return True
        except Exception as e:
            logger.error(f"Counter reset error: {e}")
            return False
    
    def get_multiple(self, counter_names: List[str]) -> Dict[str, int]:
        """
        Get multiple counter values efficiently
        """
        try:
            keys = [f"counter:{name}" for name in counter_names]
            values = self.cluster.mget(keys)
            
            result = {}
            for i, name in enumerate(counter_names):
                result[name] = int(values[i]) if values[i] else 0
            
            return result
        except Exception as e:
            logger.error(f"Multiple counter get error: {e}")
            return {name: 0 for name in counter_names}

class RealTimeAnalytics:
    """
    Real-time analytics using Redis Cluster
    """
    
    def __init__(self, cluster_client: RedisClusterClient):
        self.cluster = cluster_client.cluster
        self.counter = DistributedCounter(cluster_client)
    
    def track_page_view(self, page: str, user_id: str = None, timestamp: datetime = None):
        """
        Track page view with time-based analytics
        """
        if not timestamp:
            timestamp = datetime.now()
        
        hour_key = timestamp.strftime("%Y%m%d%H")
        day_key = timestamp.strftime("%Y%m%d")
        month_key = timestamp.strftime("%Y%m")
        
        try:
            # Overall counters
            self.counter.increment(f"page_views:{page}")
            self.counter.increment(f"page_views:{page}:hourly:{hour_key}")
            self.counter.increment(f"page_views:{page}:daily:{day_key}")
            self.counter.increment(f"page_views:{page}:monthly:{month_key}")
            
            # Unique visitors tracking
            if user_id:
                # HyperLogLog for unique visitors
                self.cluster.pfadd(f"unique_visitors:{page}:daily:{day_key}", user_id)
                self.cluster.pfadd(f"unique_visitors:{page}:monthly:{month_key}", user_id)
                
                # Set TTL for daily counters (keep for 30 days)
                self.cluster.expire(f"unique_visitors:{page}:daily:{day_key}", 30 * 24 * 3600)
            
            logger.info(f"Page view tracked: {page} by {user_id or 'anonymous'}")
            
        except Exception as e:
            logger.error(f"Page view tracking error: {e}")
    
    def get_analytics(self, page: str, period: str = "daily") -> Dict:
        """
        Get analytics for specific period
        """
        try:
            now = datetime.now()
            
            if period == "hourly":
                current_key = now.strftime("%Y%m%d%H")
                previous_key = (now - timedelta(hours=1)).strftime("%Y%m%d%H")
            elif period == "daily":
                current_key = now.strftime("%Y%m%d")
                previous_key = (now - timedelta(days=1)).strftime("%Y%m%d")
            else:  # monthly
                current_key = now.strftime("%Y%m")
                previous_key = (now - timedelta(days=30)).strftime("%Y%m")
            
            # Current period metrics
            current_views = self.counter.get_value(f"page_views:{page}:{period}:{current_key}")
            previous_views = self.counter.get_value(f"page_views:{page}:{period}:{previous_key}")
            
            # Unique visitors (daily/monthly only)
            unique_visitors = 0
            if period in ["daily", "monthly"]:
                unique_visitors = self.cluster.pfcount(f"unique_visitors:{page}:{period}:{current_key}")
            
            # Calculate growth
            growth_rate = 0
            if previous_views > 0:
                growth_rate = ((current_views - previous_views) / previous_views) * 100
            
            analytics = {
                "page": page,
                "period": period,
                "current_period": current_key,
                "views": current_views,
                "previous_views": previous_views,
                "unique_visitors": unique_visitors,
                "growth_rate": round(growth_rate, 2),
                "timestamp": now.isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Analytics get error: {e}")
            return {}
    
    def get_top_pages(self, period: str = "daily", limit: int = 10) -> List[Dict]:
        """
        Get top pages by views for current period
        """
        try:
            now = datetime.now()
            
            if period == "hourly":
                current_key = now.strftime("%Y%m%d%H")
            elif period == "daily":
                current_key = now.strftime("%Y%m%d")
            else:  # monthly
                current_key = now.strftime("%Y%m")
            
            # Pattern'e uyan key'leri bul
            pattern = f"counter:page_views:*:{period}:{current_key}"
            top_pages = []
            
            for key in self.cluster.scan_iter(match=pattern):
                try:
                    views = int(self.cluster.get(key) or 0)
                    # Key'den page name'i çıkar
                    parts = key.split(":")
                    if len(parts) >= 4:
                        page_name = parts[2]  # page_views:PAGE:period:timestamp
                        top_pages.append({"page": page_name, "views": views})
                except Exception:
                    continue
            
            # Sort by views (descending)
            top_pages.sort(key=lambda x: x["views"], reverse=True)
            return top_pages[:limit]
            
        except Exception as e:
            logger.error(f"Top pages error: {e}")
            return []

def demo_redis_cluster_production():
    """
    Production Redis Cluster demo
    """
    print("🚀 Redis Cluster Production Demo")
    print("=" * 50)
    
    # Initialize cluster client
    cluster_client = RedisClusterClient()
    
    if not cluster_client.cluster:
        print("❌ Cannot connect to Redis Cluster")
        return
    
    # Health check
    print("\n🏥 Cluster Health Check:")
    health = cluster_client.get_cluster_health()
    print(f"   Status: {health.get('status', 'unknown')}")
    print(f"   Total nodes: {health.get('total_nodes', 0)}")
    print(f"   Masters/Slaves: {health.get('master_nodes', 0)}/{health.get('slave_nodes', 0)}")
    
    if health.get('memory_usage'):
        memory = health['memory_usage']
        print(f"   Memory usage: {memory.get('usage_percentage', 0):.1f}%")
    
    # Distributed cache demo
    print("\n🗃️  Distributed Cache Demo:")
    cache = DistributedCache(cluster_client)
    
    # User session caching
    user_sessions = [
        {"session_id": "sess_123", "user_id": 1001, "login_time": datetime.now().isoformat()},
        {"session_id": "sess_456", "user_id": 1001, "login_time": datetime.now().isoformat()},
        {"session_id": "sess_789", "user_id": 1002, "login_time": datetime.now().isoformat()}
    ]
    
    for session in user_sessions:
        success = cache.cache_user_session(session["user_id"], session)
        print(f"   Session cached: {session['session_id']} → {success}")
    
    # Get user sessions
    user_1001_sessions = cache.get_user_sessions(1001)
    print(f"   User 1001 has {len(user_1001_sessions)} active sessions")
    
    # Distributed lock demo
    print("\n🔒 Distributed Lock Demo:")
    lock_manager = DistributedLock(cluster_client)
    
    # Simulate concurrent access
    def critical_section(worker_id: int):
        try:
            with lock_manager.with_lock("critical_resource", timeout=10) as lock_id:
                print(f"   Worker {worker_id} acquired lock {lock_id}")
                time.sleep(2)  # Simulate work
                print(f"   Worker {worker_id} completed work")
        except Exception as e:
            print(f"   Worker {worker_id} failed: {e}")
    
    # Start multiple workers
    threads = []
    for i in range(3):
        thread = threading.Thread(target=critical_section, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Distributed counter demo
    print("\n🔢 Distributed Counter Demo:")
    counter = DistributedCounter(cluster_client)
    
    # Reset counters
    for name in ["api_calls", "page_views", "errors"]:
        counter.reset(name)
    
    # Simulate concurrent increments
    def increment_counters(worker_id: int, iterations: int):
        for i in range(iterations):
            counter.increment("api_calls")
            if i % 10 == 0:
                counter.increment("page_views")
            if random.random() < 0.1:  # 10% error rate
                counter.increment("errors")
    
    # Multiple workers
    threads = []
    for i in range(5):
        thread = threading.Thread(target=increment_counters, args=(i+1, 100))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Get final counter values
    counters = counter.get_multiple(["api_calls", "page_views", "errors"])
    for name, value in counters.items():
        print(f"   {name}: {value}")
    
    # Real-time analytics demo
    print("\n📊 Real-time Analytics Demo:")
    analytics = RealTimeAnalytics(cluster_client)
    
    # Simulate page views
    pages = ["/home", "/products", "/about", "/contact"]
    users = [f"user_{i}" for i in range(1, 101)]
    
    print("   Generating sample page views...")
    for _ in range(500):
        page = random.choice(pages)
        user = random.choice(users)
        analytics.track_page_view(page, user)
    
    # Get analytics for each page
    for page in pages:
        page_analytics = analytics.get_analytics(page.replace("/", ""), "daily")
        if page_analytics:
            print(f"   {page}: {page_analytics.get('views', 0)} views, {page_analytics.get('unique_visitors', 0)} unique visitors")
    
    # Top pages
    top_pages = analytics.get_top_pages("daily", 3)
    print(f"   Top pages today:")
    for i, page_data in enumerate(top_pages, 1):
        print(f"     {i}. {page_data['page']}: {page_data['views']} views")
    
    print("\n✅ Redis Cluster production demo completed!")

if __name__ == "__main__":
    demo_redis_cluster_production()