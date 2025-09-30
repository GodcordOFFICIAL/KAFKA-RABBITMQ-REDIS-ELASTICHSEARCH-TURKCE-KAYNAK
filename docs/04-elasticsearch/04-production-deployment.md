# Elasticsearch Production Deployment Guide

## 📋 Özet

Bu bölümde Elasticsearch cluster'ınızı production ortamında güvenli, ölçeklenebilir ve yüksek performanslı şekilde deploy etme stratejilerini öğreneceksiniz. Cluster management, security, monitoring ve optimization konularını kapsamlı olarak ele alacağız.

## 🎯 Learning Objectives

Bu bölümü tamamladığında:

- ✅ Production-ready Elasticsearch cluster kurabileceksin
- ✅ Security configuration (authentication, authorization) yapabileceksin
- ✅ Cluster monitoring ve alerting sistemleri kuracaksın
- ✅ Index lifecycle management (ILM) uygulayabileceksin
- ✅ Backup/restore strategies implementation yapabileceksin
- ✅ Performance tuning ve optimization yapabileceksin
- ✅ Rolling upgrades ve maintenance procedures uygulayabileceksin

## 📋 Prerequisites

- Docker ve Kubernetes bilgisi
- Linux system administration
- Network ve security concepts
- Elasticsearch cluster concepts
- Monitoring tools (Prometheus, Grafana)

## 🏗️ Production Architecture

### Multi-Node Cluster Design

```yaml
# production-cluster.yml
version: "3.8"
services:
  # Master-eligible nodes (3 nodes for quorum)
  es-master-1:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-master-1
    environment:
      - node.name=es-master-1
      - node.roles=master
      - cluster.name=production-cluster
      - cluster.initial_master_nodes=es-master-1,es-master-2,es-master-3
      - discovery.seed_hosts=es-master-2,es-master-3
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
      - xpack.security.enrollment.enabled=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - es-master-1-data:/usr/share/elasticsearch/data
      - es-config:/usr/share/elasticsearch/config
    networks:
      - es-network
    ports:
      - "9200:9200"
    restart: unless-stopped

  es-master-2:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-master-2
    environment:
      - node.name=es-master-2
      - node.roles=master
      - cluster.name=production-cluster
      - cluster.initial_master_nodes=es-master-1,es-master-2,es-master-3
      - discovery.seed_hosts=es-master-1,es-master-3
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - es-master-2-data:/usr/share/elasticsearch/data
      - es-config:/usr/share/elasticsearch/config
    networks:
      - es-network
    restart: unless-stopped

  es-master-3:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-master-3
    environment:
      - node.name=es-master-3
      - node.roles=master
      - cluster.name=production-cluster
      - cluster.initial_master_nodes=es-master-1,es-master-2,es-master-3
      - discovery.seed_hosts=es-master-1,es-master-2
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - es-master-3-data:/usr/share/elasticsearch/data
      - es-config:/usr/share/elasticsearch/config
    networks:
      - es-network
    restart: unless-stopped

  # Data nodes (dedicated for data storage)
  es-data-1:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-data-1
    environment:
      - node.name=es-data-1
      - node.roles=data,ingest
      - cluster.name=production-cluster
      - discovery.seed_hosts=es-master-1,es-master-2,es-master-3
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms4g -Xmx4g"
      - xpack.security.enabled=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - es-data-1-data:/usr/share/elasticsearch/data
      - es-config:/usr/share/elasticsearch/config
    networks:
      - es-network
    restart: unless-stopped

  es-data-2:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-data-2
    environment:
      - node.name=es-data-2
      - node.roles=data,ingest
      - cluster.name=production-cluster
      - discovery.seed_hosts=es-master-1,es-master-2,es-master-3
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms4g -Xmx4g"
      - xpack.security.enabled=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - es-data-2-data:/usr/share/elasticsearch/data
      - es-config:/usr/share/elasticsearch/config
    networks:
      - es-network
    restart: unless-stopped

  # Coordinating node (for client connections)
  es-coordinating:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-coordinating
    environment:
      - node.name=es-coordinating
      - node.roles=""
      - cluster.name=production-cluster
      - discovery.seed_hosts=es-master-1,es-master-2,es-master-3
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - es-coordinating-data:/usr/share/elasticsearch/data
      - es-config:/usr/share/elasticsearch/config
    networks:
      - es-network
    ports:
      - "9201:9200"
    restart: unless-stopped

  # Kibana for visualization
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://es-coordinating:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}
      - xpack.security.enabled=true
      - xpack.encryptedSavedObjects.encryptionKey=${KIBANA_ENCRYPTION_KEY}
    ports:
      - "5601:5601"
    networks:
      - es-network
    depends_on:
      - es-coordinating
    restart: unless-stopped

  # Metricbeat for monitoring
  metricbeat:
    image: docker.elastic.co/beats/metricbeat:8.11.0
    container_name: metricbeat
    user: root
    command: metricbeat -e -strict.perms=false
    environment:
      - ELASTICSEARCH_HOSTS=http://es-coordinating:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}
    volumes:
      - ./monitoring/metricbeat.yml:/usr/share/metricbeat/metricbeat.yml:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /sys/fs/cgroup:/hostfs/sys/fs/cgroup:ro
      - /proc:/hostfs/proc:ro
      - /:/hostfs:ro
    networks:
      - es-network
    depends_on:
      - es-coordinating
    restart: unless-stopped

volumes:
  es-master-1-data:
  es-master-2-data:
  es-master-3-data:
  es-data-1-data:
  es-data-2-data:
  es-coordinating-data:
  es-config:

networks:
  es-network:
    driver: bridge
```

### Kubernetes Deployment

```yaml
# elasticsearch-cluster.yaml
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: production-cluster
  namespace: elastic-system
spec:
  version: 8.11.0

  # Master nodes
  nodeSets:
    - name: master
      count: 3
      config:
        node.roles: ["master"]
        cluster.routing.allocation.disk.threshold_enabled: false
      podTemplate:
        spec:
          containers:
            - name: elasticsearch
              env:
                - name: ES_JAVA_OPTS
                  value: "-Xms2g -Xmx2g"
              resources:
                requests:
                  memory: 4Gi
                  cpu: 1
                limits:
                  memory: 4Gi
                  cpu: 2
      volumeClaimTemplates:
        - metadata:
            name: elasticsearch-data
          spec:
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 50Gi
            storageClassName: fast-ssd

    # Data nodes
    - name: data
      count: 3
      config:
        node.roles: ["data", "ingest"]
        cluster.routing.allocation.disk.threshold_enabled: true
        cluster.routing.allocation.disk.watermark.low: "85%"
        cluster.routing.allocation.disk.watermark.high: "90%"
        cluster.routing.allocation.disk.watermark.flood_stage: "95%"
      podTemplate:
        spec:
          containers:
            - name: elasticsearch
              env:
                - name: ES_JAVA_OPTS
                  value: "-Xms8g -Xmx8g"
              resources:
                requests:
                  memory: 16Gi
                  cpu: 2
                limits:
                  memory: 16Gi
                  cpu: 4
      volumeClaimTemplates:
        - metadata:
            name: elasticsearch-data
          spec:
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 500Gi
            storageClassName: fast-ssd

    # Coordinating nodes
    - name: coordinating
      count: 2
      config:
        node.roles: []
      podTemplate:
        spec:
          containers:
            - name: elasticsearch
              env:
                - name: ES_JAVA_OPTS
                  value: "-Xms4g -Xmx4g"
              resources:
                requests:
                  memory: 8Gi
                  cpu: 1
                limits:
                  memory: 8Gi
                  cpu: 2
      volumeClaimTemplates:
        - metadata:
            name: elasticsearch-data
          spec:
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 10Gi
            storageClassName: standard

  http:
    service:
      spec:
        type: LoadBalancer
        ports:
          - port: 9200
            targetPort: 9200
    tls:
      selfSignedCertificate:
        disabled: false

---
apiVersion: kibana.k8s.elastic.co/v1
kind: Kibana
metadata:
  name: kibana
  namespace: elastic-system
spec:
  version: 8.11.0
  count: 2
  elasticsearchRef:
    name: production-cluster
  http:
    service:
      spec:
        type: LoadBalancer
    tls:
      selfSignedCertificate:
        disabled: false
  podTemplate:
    spec:
      containers:
        - name: kibana
          resources:
            requests:
              memory: 2Gi
              cpu: 1
            limits:
              memory: 4Gi
              cpu: 2
```

## 🔐 Security Configuration

### X-Pack Security Setup

```bash
#!/bin/bash
# security-setup.sh

# Generate certificates
docker exec es-master-1 /usr/share/elasticsearch/bin/elasticsearch-certutil ca --silent --pem -out /tmp/ca.zip
docker exec es-master-1 unzip /tmp/ca.zip -d /tmp/

# Generate node certificates
docker exec es-master-1 /usr/share/elasticsearch/bin/elasticsearch-certutil cert \
  --silent --pem --ca-cert /tmp/ca/ca.crt --ca-key /tmp/ca/ca.key \
  --dns es-master-1,es-master-2,es-master-3,es-data-1,es-data-2,es-coordinating \
  --ip 127.0.0.1 \
  -out /tmp/certs.zip

# Extract certificates
docker exec es-master-1 unzip /tmp/certs.zip -d /tmp/

# Copy certificates to config
docker exec es-master-1 cp /tmp/ca/ca.crt /usr/share/elasticsearch/config/
docker exec es-master-1 cp /tmp/instance/instance.crt /usr/share/elasticsearch/config/
docker exec es-master-1 cp /tmp/instance/instance.key /usr/share/elasticsearch/config/

echo "🔐 Certificates generated successfully!"
```

### User Management

```python
# security_management.py
from elasticsearch import Elasticsearch
import json

class ElasticsearchSecurity:
    """
    Elasticsearch security management
    """

    def __init__(self, hosts=['localhost:9200'], username='elastic', password='password'):
        self.es = Elasticsearch(
            hosts,
            basic_auth=(username, password),
            verify_certs=True,
            ca_certs='/path/to/ca.crt'
        )

    def create_user(self, username: str, password: str, roles: list, full_name: str = None):
        """
        Create new user
        """
        user_body = {
            "password": password,
            "roles": roles,
            "full_name": full_name or username
        }

        try:
            response = self.es.security.put_user(username=username, body=user_body)
            print(f"✅ User '{username}' created successfully")
            return response
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None

    def create_role(self, role_name: str, cluster_privileges: list,
                   index_privileges: dict, applications: list = None):
        """
        Create custom role
        """
        role_body = {
            "cluster": cluster_privileges,
            "indices": [
                {
                    "names": list(index_privileges.keys()),
                    "privileges": list(index_privileges.values())
                }
            ]
        }

        if applications:
            role_body["applications"] = applications

        try:
            response = self.es.security.put_role(name=role_name, body=role_body)
            print(f"✅ Role '{role_name}' created successfully")
            return response
        except Exception as e:
            print(f"❌ Error creating role: {e}")
            return None

    def setup_production_users(self):
        """
        Setup production users and roles
        """
        print("🔐 Setting up production users and roles...")

        # Custom roles
        roles_config = {
            "read_only_analyst": {
                "cluster": ["monitor"],
                "indices": {
                    "logs-*,metrics-*": ["read", "view_index_metadata"]
                }
            },
            "data_engineer": {
                "cluster": ["monitor", "manage_index_templates"],
                "indices": {
                    "*": ["read", "write", "create_index", "manage"]
                }
            },
            "application_writer": {
                "cluster": ["monitor"],
                "indices": {
                    "app-logs-*,app-metrics-*": ["read", "write", "create_index"]
                }
            }
        }

        # Create roles
        for role_name, config in roles_config.items():
            self.create_role(role_name, config["cluster"], config["indices"])

        # Create users
        users_config = [
            {
                "username": "analyst_user",
                "password": "AnalystPass123!",
                "roles": ["read_only_analyst"],
                "full_name": "Data Analyst"
            },
            {
                "username": "engineer_user",
                "password": "EngineerPass123!",
                "roles": ["data_engineer"],
                "full_name": "Data Engineer"
            },
            {
                "username": "app_writer",
                "password": "AppWriterPass123!",
                "roles": ["application_writer"],
                "full_name": "Application Writer"
            }
        ]

        for user_config in users_config:
            self.create_user(**user_config)

        print("✅ Production users and roles setup completed!")

# Security setup example
def setup_security():
    security = ElasticsearchSecurity()
    security.setup_production_users()

if __name__ == "__main__":
    setup_security()
```

## 📊 Monitoring ve Alerting

### Metricbeat Configuration

```yaml
# monitoring/metricbeat.yml
metricbeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: false

metricbeat.modules:
  # Elasticsearch module
  - module: elasticsearch
    metricsets:
      - node
      - node_stats
      - cluster_stats
      - index
      - index_recovery
      - index_summary
      - shard
      - ml_job
    period: 10s
    hosts: ["http://es-coordinating:9200"]
    username: "elastic"
    password: "${ELASTIC_PASSWORD}"
    xpack.enabled: true

  # System module
  - module: system
    metricsets:
      - cpu
      - load
      - memory
      - network
      - process
      - process_summary
      - socket_summary
      - filesystem
      - fsstat
      - diskio
    enabled: true
    period: 10s
    processes: [".*"]

  # Docker module
  - module: docker
    metricsets:
      - container
      - cpu
      - diskio
      - info
      - memory
      - network
    hosts: ["unix:///var/run/docker.sock"]
    period: 10s
    enabled: true

processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_docker_metadata: ~

output.elasticsearch:
  hosts: ["http://es-coordinating:9200"]
  username: "elastic"
  password: "${ELASTIC_PASSWORD}"
  index: "metricbeat-%{[agent.version]}-%{+yyyy.MM.dd}"

setup.template.settings:
  index.number_of_shards: 1
  index.codec: best_compression

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/metricbeat
  name: metricbeat
  keepfiles: 7
  permissions: 0644
```

### Alerting Rules

```python
# monitoring/alerting.py
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import json

class ElasticsearchAlerting:
    """
    Elasticsearch cluster alerting system
    """

    def __init__(self, hosts=['localhost:9200'], **kwargs):
        self.es = Elasticsearch(hosts, **kwargs)

    def create_watcher_alerts(self):
        """
        Create production watcher alerts
        """
        print("🚨 Creating production alerts...")

        # High CPU usage alert
        cpu_alert = {
            "trigger": {
                "schedule": {
                    "interval": "1m"
                }
            },
            "input": {
                "search": {
                    "request": {
                        "search_type": "query_then_fetch",
                        "indices": ["metricbeat-*"],
                        "body": {
                            "query": {
                                "bool": {
                                    "must": [
                                        {
                                            "term": {
                                                "metricset.name": "node_stats"
                                            }
                                        },
                                        {
                                            "range": {
                                                "@timestamp": {
                                                    "gte": "now-5m"
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            "aggs": {
                                "avg_cpu": {
                                    "avg": {
                                        "field": "elasticsearch.node.process.cpu.percent"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "condition": {
                "compare": {
                    "ctx.payload.aggregations.avg_cpu.value": {
                        "gt": 80
                    }
                }
            },
            "actions": {
                "send_email": {
                    "email": {
                        "to": ["admin@company.com"],
                        "subject": "High CPU Usage Alert",
                        "body": "Elasticsearch cluster CPU usage is {{ctx.payload.aggregations.avg_cpu.value}}%"
                    }
                },
                "log_alert": {
                    "logging": {
                        "text": "High CPU usage detected: {{ctx.payload.aggregations.avg_cpu.value}}%"
                    }
                }
            }
        }

        # Disk space alert
        disk_alert = {
            "trigger": {
                "schedule": {
                    "interval": "5m"
                }
            },
            "input": {
                "search": {
                    "request": {
                        "indices": ["metricbeat-*"],
                        "body": {
                            "query": {
                                "bool": {
                                    "must": [
                                        {
                                            "term": {
                                                "metricset.name": "node_stats"
                                            }
                                        },
                                        {
                                            "range": {
                                                "@timestamp": {
                                                    "gte": "now-10m"
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            "aggs": {
                                "nodes": {
                                    "terms": {
                                        "field": "elasticsearch.node.name"
                                    },
                                    "aggs": {
                                        "disk_usage": {
                                            "max": {
                                                "field": "elasticsearch.node.fs.total.total_in_bytes"
                                            }
                                        },
                                        "disk_available": {
                                            "max": {
                                                "field": "elasticsearch.node.fs.total.available_in_bytes"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "condition": {
                "script": {
                    "source": """
                    for (bucket in ctx.payload.aggregations.nodes.buckets) {
                        def used = bucket.disk_usage.value - bucket.disk_available.value;
                        def usage_percent = (used / bucket.disk_usage.value) * 100;
                        if (usage_percent > 85) {
                            return true;
                        }
                    }
                    return false;
                    """
                }
            },
            "actions": {
                "send_alert": {
                    "email": {
                        "to": ["admin@company.com"],
                        "subject": "Disk Space Alert",
                        "body": "One or more Elasticsearch nodes have high disk usage"
                    }
                }
            }
        }

        # Cluster health alert
        health_alert = {
            "trigger": {
                "schedule": {
                    "interval": "30s"
                }
            },
            "input": {
                "http": {
                    "request": {
                        "scheme": "http",
                        "host": "es-coordinating",
                        "port": 9200,
                        "method": "get",
                        "path": "/_cluster/health"
                    }
                }
            },
            "condition": {
                "compare": {
                    "ctx.payload.status": {
                        "not_eq": "green"
                    }
                }
            },
            "actions": {
                "send_alert": {
                    "email": {
                        "to": ["admin@company.com"],
                        "subject": "Cluster Health Alert",
                        "body": "Elasticsearch cluster health is {{ctx.payload.status}}"
                    }
                }
            }
        }

        # Create watchers
        alerts = {
            "high_cpu_usage": cpu_alert,
            "disk_space_warning": disk_alert,
            "cluster_health_check": health_alert
        }

        for alert_name, alert_config in alerts.items():
            try:
                self.es.watcher.put_watch(id=alert_name, body=alert_config)
                print(f"✅ Alert '{alert_name}' created successfully")
            except Exception as e:
                print(f"❌ Error creating alert '{alert_name}': {e}")

    def check_cluster_health(self):
        """
        Manual cluster health check
        """
        try:
            health = self.es.cluster.health()

            print(f"🏥 Cluster Health Report:")
            print(f"   Status: {health['status']}")
            print(f"   Active Shards: {health['active_shards']}")
            print(f"   Relocating Shards: {health['relocating_shards']}")
            print(f"   Initializing Shards: {health['initializing_shards']}")
            print(f"   Unassigned Shards: {health['unassigned_shards']}")
            print(f"   Number of Nodes: {health['number_of_nodes']}")
            print(f"   Number of Data Nodes: {health['number_of_data_nodes']}")

            # Check for issues
            if health['status'] == 'red':
                print("🔴 CRITICAL: Cluster is in RED state!")
            elif health['status'] == 'yellow':
                print("🟡 WARNING: Cluster is in YELLOW state")
            else:
                print("🟢 OK: Cluster is healthy")

            return health

        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return None

def setup_monitoring():
    alerting = ElasticsearchAlerting()
    alerting.create_watcher_alerts()
    alerting.check_cluster_health()

if __name__ == "__main__":
    setup_monitoring()
```

## 🔄 Index Lifecycle Management (ILM)

### ILM Policies

```python
# ilm_management.py
from elasticsearch import Elasticsearch
import json

class IndexLifecycleManager:
    """
    Elasticsearch Index Lifecycle Management
    """

    def __init__(self, hosts=['localhost:9200'], **kwargs):
        self.es = Elasticsearch(hosts, **kwargs)

    def create_log_retention_policy(self):
        """
        Create log retention ILM policy
        """
        policy = {
            "policy": {
                "phases": {
                    "hot": {
                        "min_age": "0ms",
                        "actions": {
                            "rollover": {
                                "max_size": "50GB",
                                "max_age": "7d",
                                "max_docs": 10000000
                            },
                            "set_priority": {
                                "priority": 100
                            }
                        }
                    },
                    "warm": {
                        "min_age": "7d",
                        "actions": {
                            "set_priority": {
                                "priority": 50
                            },
                            "allocate": {
                                "number_of_replicas": 0
                            },
                            "shrink": {
                                "number_of_shards": 1
                            },
                            "forcemerge": {
                                "max_num_segments": 1
                            }
                        }
                    },
                    "cold": {
                        "min_age": "30d",
                        "actions": {
                            "set_priority": {
                                "priority": 10
                            },
                            "allocate": {
                                "number_of_replicas": 0,
                                "require": {
                                    "data_tier": "cold"
                                }
                            }
                        }
                    },
                    "delete": {
                        "min_age": "90d",
                        "actions": {
                            "delete": {}
                        }
                    }
                }
            }
        }

        try:
            response = self.es.ilm.put_lifecycle(name="logs-policy", body=policy)
            print("✅ Log retention ILM policy created")
            return response
        except Exception as e:
            print(f"❌ Error creating ILM policy: {e}")
            return None

    def create_metrics_policy(self):
        """
        Create metrics retention ILM policy
        """
        policy = {
            "policy": {
                "phases": {
                    "hot": {
                        "min_age": "0ms",
                        "actions": {
                            "rollover": {
                                "max_size": "20GB",
                                "max_age": "1d"
                            },
                            "set_priority": {
                                "priority": 100
                            }
                        }
                    },
                    "warm": {
                        "min_age": "1d",
                        "actions": {
                            "set_priority": {
                                "priority": 50
                            },
                            "allocate": {
                                "number_of_replicas": 0
                            },
                            "forcemerge": {
                                "max_num_segments": 1
                            }
                        }
                    },
                    "cold": {
                        "min_age": "7d",
                        "actions": {
                            "set_priority": {
                                "priority": 10
                            }
                        }
                    },
                    "delete": {
                        "min_age": "30d",
                        "actions": {
                            "delete": {}
                        }
                    }
                }
            }
        }

        try:
            response = self.es.ilm.put_lifecycle(name="metrics-policy", body=policy)
            print("✅ Metrics retention ILM policy created")
            return response
        except Exception as e:
            print(f"❌ Error creating metrics ILM policy: {e}")
            return None

    def create_index_templates(self):
        """
        Create index templates with ILM policies
        """
        # Logs template
        logs_template = {
            "index_patterns": ["logs-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                    "index.lifecycle.name": "logs-policy",
                    "index.lifecycle.rollover_alias": "logs-alias"
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {
                            "type": "date"
                        },
                        "level": {
                            "type": "keyword"
                        },
                        "message": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "service": {
                            "type": "keyword"
                        },
                        "host": {
                            "type": "keyword"
                        }
                    }
                }
            }
        }

        # Metrics template
        metrics_template = {
            "index_patterns": ["metrics-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                    "index.lifecycle.name": "metrics-policy",
                    "index.lifecycle.rollover_alias": "metrics-alias"
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {
                            "type": "date"
                        },
                        "metric_name": {
                            "type": "keyword"
                        },
                        "value": {
                            "type": "double"
                        },
                        "tags": {
                            "type": "object"
                        },
                        "host": {
                            "type": "keyword"
                        }
                    }
                }
            }
        }

        try:
            # Create templates
            self.es.indices.put_index_template(name="logs-template", body=logs_template)
            self.es.indices.put_index_template(name="metrics-template", body=metrics_template)

            print("✅ Index templates created successfully")

        except Exception as e:
            print(f"❌ Error creating index templates: {e}")

    def setup_ilm_management(self):
        """
        Complete ILM setup
        """
        print("🔄 Setting up Index Lifecycle Management...")

        # Create policies
        self.create_log_retention_policy()
        self.create_metrics_policy()

        # Create templates
        self.create_index_templates()

        # Create initial indices with aliases
        try:
            # Create logs alias
            self.es.indices.create(
                index="logs-000001",
                body={
                    "aliases": {
                        "logs-alias": {
                            "is_write_index": True
                        }
                    }
                }
            )

            # Create metrics alias
            self.es.indices.create(
                index="metrics-000001",
                body={
                    "aliases": {
                        "metrics-alias": {
                            "is_write_index": True
                        }
                    }
                }
            )

            print("✅ ILM management setup completed")

        except Exception as e:
            print(f"❌ Error setting up aliases: {e}")

def setup_ilm():
    ilm_manager = IndexLifecycleManager()
    ilm_manager.setup_ilm_management()

if __name__ == "__main__":
    setup_ilm()
```

## 💾 Backup ve Restore

### Snapshot Repository

```python
# backup_restore.py
from elasticsearch import Elasticsearch
from datetime import datetime
import json

class ElasticsearchBackup:
    """
    Elasticsearch backup and restore management
    """

    def __init__(self, hosts=['localhost:9200'], **kwargs):
        self.es = Elasticsearch(hosts, **kwargs)

    def create_snapshot_repository(self, repo_name: str, repo_path: str):
        """
        Create snapshot repository
        """
        repo_config = {
            "type": "fs",
            "settings": {
                "location": repo_path,
                "compress": True,
                "chunk_size": "1gb",
                "max_restore_bytes_per_sec": "40mb",
                "max_snapshot_bytes_per_sec": "40mb"
            }
        }

        try:
            response = self.es.snapshot.create_repository(
                repository=repo_name,
                body=repo_config
            )
            print(f"✅ Snapshot repository '{repo_name}' created")
            return response
        except Exception as e:
            print(f"❌ Error creating repository: {e}")
            return None

    def create_snapshot(self, repo_name: str, snapshot_name: str = None,
                       indices: str = "*", ignore_unavailable: bool = True):
        """
        Create cluster snapshot
        """
        if not snapshot_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_name = f"snapshot_{timestamp}"

        snapshot_config = {
            "indices": indices,
            "ignore_unavailable": ignore_unavailable,
            "include_global_state": True,
            "metadata": {
                "taken_by": "elasticsearch_backup_system",
                "taken_because": "Scheduled backup"
            }
        }

        try:
            response = self.es.snapshot.create(
                repository=repo_name,
                snapshot=snapshot_name,
                body=snapshot_config,
                wait_for_completion=False
            )
            print(f"✅ Snapshot '{snapshot_name}' started")
            return response
        except Exception as e:
            print(f"❌ Error creating snapshot: {e}")
            return None

    def restore_snapshot(self, repo_name: str, snapshot_name: str,
                        indices: str = None, rename_pattern: str = None):
        """
        Restore from snapshot
        """
        restore_config = {
            "ignore_unavailable": True,
            "include_global_state": False
        }

        if indices:
            restore_config["indices"] = indices

        if rename_pattern:
            restore_config["rename_pattern"] = rename_pattern
            restore_config["rename_replacement"] = "restored_$1"

        try:
            response = self.es.snapshot.restore(
                repository=repo_name,
                snapshot=snapshot_name,
                body=restore_config,
                wait_for_completion=False
            )
            print(f"✅ Restore from '{snapshot_name}' started")
            return response
        except Exception as e:
            print(f"❌ Error restoring snapshot: {e}")
            return None

    def list_snapshots(self, repo_name: str):
        """
        List all snapshots in repository
        """
        try:
            response = self.es.snapshot.get(
                repository=repo_name,
                snapshot="_all"
            )

            snapshots = response.get('snapshots', [])
            print(f"📋 Snapshots in '{repo_name}':")

            for snapshot in snapshots:
                name = snapshot['snapshot']
                state = snapshot['state']
                start_time = snapshot['start_time']
                duration = snapshot.get('duration_in_millis', 0) / 1000

                print(f"   📸 {name} - {state} ({start_time}) - Duration: {duration}s")

            return snapshots

        except Exception as e:
            print(f"❌ Error listing snapshots: {e}")
            return []

    def delete_old_snapshots(self, repo_name: str, keep_count: int = 7):
        """
        Delete old snapshots, keep only recent ones
        """
        try:
            snapshots = self.list_snapshots(repo_name)

            if len(snapshots) <= keep_count:
                print(f"✅ No old snapshots to delete (keeping {keep_count})")
                return

            # Sort by start time and get old snapshots
            snapshots.sort(key=lambda x: x['start_time'], reverse=True)
            old_snapshots = snapshots[keep_count:]

            for snapshot in old_snapshots:
                snapshot_name = snapshot['snapshot']

                try:
                    self.es.snapshot.delete(
                        repository=repo_name,
                        snapshot=snapshot_name
                    )
                    print(f"🗑️  Deleted old snapshot: {snapshot_name}")
                except Exception as e:
                    print(f"❌ Error deleting snapshot {snapshot_name}: {e}")

            print(f"✅ Cleanup completed, kept {keep_count} snapshots")

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

    def setup_automated_backup(self, repo_name: str = "backup-repo",
                              repo_path: str = "/usr/share/elasticsearch/backups"):
        """
        Setup automated backup system
        """
        print("💾 Setting up automated backup system...")

        # Create repository
        self.create_snapshot_repository(repo_name, repo_path)

        # Create initial snapshot
        snapshot_name = f"initial_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.create_snapshot(repo_name, snapshot_name)

        print("✅ Automated backup system setup completed")

def setup_backup():
    backup_manager = ElasticsearchBackup()
    backup_manager.setup_automated_backup()

if __name__ == "__main__":
    setup_backup()
```

## ✅ Checklist

Bu bölümü tamamladıktan sonra:

- [ ] Production-ready cluster kurabiliyorum
- [ ] Security configuration yapabiliyorum
- [ ] Monitoring ve alerting sistemi kurabiliyorum
- [ ] ILM policies uygulayabiliyorum
- [ ] Backup/restore strategies implementation yapabiliyorum
- [ ] Performance tuning yapabiliyorum
- [ ] Rolling upgrades uygulayabiliyorum
- [ ] Incident response procedures biliyorum

## ⚠️ Production Best Practices

### 1. Hardware Sizing

- **Master Nodes**: 3 dedicated nodes, 8GB RAM, 2 CPU cores
- **Data Nodes**: 8-32GB RAM, 4-8 CPU cores, SSD storage
- **Coordinating Nodes**: 4-8GB RAM, 2-4 CPU cores

### 2. JVM Settings

```bash
# JVM heap size (50% of RAM, max 31GB)
-Xms16g
-Xmx16g

# GC settings
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:+UnlockExperimentalVMOptions
-XX:+UseG1GC
-XX:G1HeapRegionSize=32m
```

### 3. Operating System

- Disable swap: `swapoff -a`
- Increase file descriptors: `ulimit -n 65536`
- Virtual memory: `vm.max_map_count=262144`

## 🔗 İlgili Bölümler

- **Önceki**: [Search ve Aggregations](03-search-aggregations.md)
- **Sonraki**: [Integration Examples](../05-integration/README.md)
- **İlgili**: [Redis Production](../03-redis/06-clustering-production.md)

---

**Sonraki Adım**: Teknolojilerin entegrasyonu için [Integration Examples](../05-integration/README.md) bölümüne geçin! 🚀
