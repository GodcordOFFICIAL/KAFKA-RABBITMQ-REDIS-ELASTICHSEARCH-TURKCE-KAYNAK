# examples/elasticsearch/python/basic_operations.py
from elasticsearch import Elasticsearch
import json
from datetime import datetime
from typing import Dict, List, Optional

class ElasticsearchBasics:
    def __init__(self):
        # Elasticsearch client oluştur
        self.es = Elasticsearch(
            [{'host': 'localhost', 'port': 9200, 'scheme': 'http'}],
            # Security disabled for development
            verify_certs=False,
            ssl_show_warn=False
        )
        
        # Bağlantı testi
        try:
            if self.es.ping():
                print("✅ Elasticsearch bağlantısı başarılı!")
                cluster_info = self.es.info()
                print(f"📊 Cluster: {cluster_info['cluster_name']}")
                print(f"📦 Version: {cluster_info['version']['number']}")
            else:
                raise ConnectionError("Elasticsearch'a bağlanılamadı")
        except Exception as e:
            print(f"❌ Elasticsearch bağlantı hatası: {str(e)}")
            raise

    def demo_index_operations(self):
        """Index operasyonları demo"""
        print("\n📚 INDEX OPERATIONS DEMO")
        print("=" * 40)
        
        index_name = "demo-users"
        
        # 1. Index oluştur
        if self.es.indices.exists(index=index_name):
            self.es.indices.delete(index=index_name)
            print(f"🗑️ Eski index silindi: {index_name}")
        
        # Index settings ve mappings ile oluştur
        index_body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "turkish_analyzer": {
                            "type": "standard",
                            "stopwords": "_turkish_"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "turkish_analyzer"
                    },
                    "email": {
                        "type": "keyword"  # Exact match için
                    },
                    "age": {
                        "type": "integer"
                    },
                    "city": {
                        "type": "keyword"
                    },
                    "bio": {
                        "type": "text",
                        "analyzer": "turkish_analyzer"
                    },
                    "created_at": {
                        "type": "date"
                    },
                    "tags": {
                        "type": "keyword"
                    },
                    "score": {
                        "type": "float"
                    }
                }
            }
        }
        
        self.es.indices.create(index=index_name, body=index_body)
        print(f"✅ Index oluşturuldu: {index_name}")
        
        # 2. Index bilgilerini al
        index_info = self.es.indices.get(index=index_name)
        settings = index_info[index_name]['settings']
        print(f"🔧 Shards: {settings['index']['number_of_shards']}")
        print(f"🔧 Replicas: {settings['index']['number_of_replicas']}")
        
        return index_name

    def demo_document_operations(self, index_name: str):
        """Document operasyonları demo"""
        print("\n📄 DOCUMENT OPERATIONS DEMO")
        print("=" * 40)
        
        # 1. Tek document ekle (ID belirtili)
        user_doc = {
            "name": "Ahmet Yılmaz",
            "email": "ahmet@example.com",
            "age": 25,
            "city": "Istanbul",
            "bio": "Yazılım geliştirici ve teknoloji meraklısı",
            "created_at": datetime.now().isoformat(),
            "tags": ["developer", "python", "elasticsearch"],
            "score": 85.5
        }
        
        result = self.es.index(
            index=index_name,
            id="user_001",
            body=user_doc
        )
        
        print(f"✅ Document eklendi:")
        print(f"   ID: {result['_id']}")
        print(f"   Version: {result['_version']}")
        print(f"   Result: {result['result']}")
        
        # 2. Otomatik ID ile document ekle
        user_doc2 = {
            "name": "Fatma Kaya",
            "email": "fatma@example.com",
            "age": 30,
            "city": "Ankara",
            "bio": "UX tasarımcısı ve dijital pazarlama uzmanı",
            "created_at": datetime.now().isoformat(),
            "tags": ["designer", "ux", "marketing"],
            "score": 92.0
        }
        
        result2 = self.es.index(index=index_name, body=user_doc2)
        auto_id = result2['_id']
        print(f"✅ Otomatik ID ile document eklendi: {auto_id}")
        
        # 3. Bulk insert (birden fazla document)
        bulk_users = [
            {
                "name": "Mehmet Demir",
                "email": "mehmet@example.com",
                "age": 28,
                "city": "Izmir",
                "bio": "Backend developer ve sistem yöneticisi",
                "created_at": datetime.now().isoformat(),
                "tags": ["developer", "backend", "devops"],
                "score": 88.0
            },
            {
                "name": "Ayşe Şahin",
                "email": "ayse@example.com",
                "age": 22,
                "city": "Istanbul",
                "bio": "Frontend developer ve UI uzmanı",
                "created_at": datetime.now().isoformat(),
                "tags": ["developer", "frontend", "react"],
                "score": 90.5
            },
            {
                "name": "Can Öztürk",
                "email": "can@example.com",
                "age": 35,
                "city": "Bursa",
                "bio": "Proje yöneticisi ve agile coach",
                "created_at": datetime.now().isoformat(),
                "tags": ["manager", "agile", "scrum"],
                "score": 87.5
            }
        ]
        
        # Bulk API kullanımı
        bulk_body = []
        for i, user in enumerate(bulk_users, 3):
            bulk_body.extend([
                {"index": {"_index": index_name, "_id": f"user_{i:03d}"}},
                user
            ])
        
        bulk_result = self.es.bulk(body=bulk_body)
        
        successful = sum(1 for item in bulk_result['items'] if item['index']['status'] == 201)
        print(f"✅ Bulk insert: {successful} document eklendi")
        
        # 4. Document al
        doc_result = self.es.get(index=index_name, id="user_001")
        print(f"\n📄 Document detayları:")
        print(f"   Name: {doc_result['_source']['name']}")
        print(f"   Email: {doc_result['_source']['email']}")
        print(f"   City: {doc_result['_source']['city']}")
        
        # 5. Document güncelle
        update_body = {
            "doc": {
                "age": 26,  # Yaş güncelle
                "score": 87.0,  # Skor güncelle
                "updated_at": datetime.now().isoformat()
            }
        }
        
        update_result = self.es.update(
            index=index_name,
            id="user_001",
            body=update_body
        )
        
        print(f"✅ Document güncellendi:")
        print(f"   Version: {update_result['_version']}")
        print(f"   Result: {update_result['result']}")
        
        return auto_id

    def demo_search_operations(self, index_name: str):
        """Arama operasyonları demo"""
        print("\n🔍 SEARCH OPERATIONS DEMO")
        print("=" * 40)
        
        # Index'in refresh olmasını bekle
        self.es.indices.refresh(index=index_name)
        
        # 1. Match All Query (tüm document'ları al)
        search_body = {
            "query": {
                "match_all": {}
            }
        }
        
        result = self.es.search(index=index_name, body=search_body)
        total_docs = result['hits']['total']['value']
        print(f"📊 Toplam document sayısı: {total_docs}")
        
        # 2. Match Query (text arama)
        search_body = {
            "query": {
                "match": {
                    "bio": "developer"
                }
            }
        }
        
        result = self.es.search(index=index_name, body=search_body)
        print(f"\n🔍 'developer' araması:")
        print(f"   Bulunan: {result['hits']['total']['value']} document")
        
        for hit in result['hits']['hits']:
            source = hit['_source']
            print(f"   - {source['name']} ({source['city']})")
        
        # 3. Term Query (exact match)
        search_body = {
            "query": {
                "term": {
                    "city.keyword": "Istanbul"
                }
            }
        }
        
        result = self.es.search(index=index_name, body=search_body)
        print(f"\n🏙️ Istanbul'daki kullanıcılar:")
        for hit in result['hits']['hits']:
            source = hit['_source']
            print(f"   - {source['name']} (Score: {source['score']})")
        
        # 4. Range Query (aralık araması)
        search_body = {
            "query": {
                "range": {
                    "age": {
                        "gte": 25,  # 25 ve üzeri
                        "lte": 30   # 30 ve altı
                    }
                }
            },
            "sort": [
                {"age": {"order": "asc"}}
            ]
        }
        
        result = self.es.search(index=index_name, body=search_body)
        print(f"\n👥 25-30 yaş arası kullanıcılar:")
        for hit in result['hits']['hits']:
            source = hit['_source']
            print(f"   - {source['name']}: {source['age']} yaş")
        
        # 5. Bool Query (complex queries)
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"bio": "developer"}}
                    ],
                    "filter": [
                        {"range": {"score": {"gte": 85}}}
                    ],
                    "must_not": [
                        {"term": {"city.keyword": "Bursa"}}
                    ]
                }
            },
            "sort": [
                {"score": {"order": "desc"}}
            ]
        }
        
        result = self.es.search(index=index_name, body=search_body)
        print(f"\n🎯 Complex query (developer + score >= 85 + not Bursa):")
        for hit in result['hits']['hits']:
            source = hit['_source']
            print(f"   - {source['name']}: {source['score']} ({source['city']})")

    def demo_aggregations(self, index_name: str):
        """Aggregation operasyonları demo"""
        print("\n📊 AGGREGATIONS DEMO")
        print("=" * 40)
        
        # 1. Terms Aggregation (şehire göre grupla)
        agg_body = {
            "size": 0,  # Sadece aggregation sonuçları
            "aggs": {
                "users_by_city": {
                    "terms": {
                        "field": "city.keyword"
                    }
                }
            }
        }
        
        result = self.es.search(index=index_name, body=agg_body)
        city_buckets = result['aggregations']['users_by_city']['buckets']
        
        print("🏙️ Şehire göre kullanıcı dağılımı:")
        for bucket in city_buckets:
            print(f"   {bucket['key']}: {bucket['doc_count']} kullanıcı")
        
        # 2. Stats Aggregation (yaş istatistikleri)
        agg_body = {
            "size": 0,
            "aggs": {
                "age_stats": {
                    "stats": {
                        "field": "age"
                    }
                }
            }
        }
        
        result = self.es.search(index=index_name, body=agg_body)
        age_stats = result['aggregations']['age_stats']
        
        print(f"\n📈 Yaş istatistikleri:")
        print(f"   Ortalama: {age_stats['avg']:.1f}")
        print(f"   Min: {age_stats['min']}")
        print(f"   Max: {age_stats['max']}")
        print(f"   Toplam: {age_stats['count']}")
        
        # 3. Histogram Aggregation (skor dağılımı)
        agg_body = {
            "size": 0,
            "aggs": {
                "score_histogram": {
                    "histogram": {
                        "field": "score",
                        "interval": 5
                    }
                }
            }
        }
        
        result = self.es.search(index=index_name, body=agg_body)
        score_buckets = result['aggregations']['score_histogram']['buckets']
        
        print(f"\n📊 Skor dağılımı (5'lik gruplar):")
        for bucket in score_buckets:
            if bucket['doc_count'] > 0:
                print(f"   {bucket['key']}-{bucket['key']+5}: {bucket['doc_count']} kullanıcı")

    def cleanup_demo_data(self, index_name: str):
        """Demo verilerini temizle"""
        print(f"\n🧹 CLEANUP DEMO DATA")
        print("=" * 40)
        
        if self.es.indices.exists(index=index_name):
            self.es.indices.delete(index=index_name)
            print(f"🗑️ Index silindi: {index_name}")
        else:
            print(f"ℹ️ Index bulunamadı: {index_name}")

    def run_all_demos(self):
        """Tüm demo'ları çalıştır"""
        print("🔍 Elasticsearch Basics Demo başlıyor...\n")
        
        try:
            # 1. Index operations
            index_name = self.demo_index_operations()
            
            # 2. Document operations
            auto_id = self.demo_document_operations(index_name)
            
            # 3. Search operations
            self.demo_search_operations(index_name)
            
            # 4. Aggregations
            self.demo_aggregations(index_name)
            
            print("\n✅ Tüm demo'lar başarıyla tamamlandı!")
            
            # Cleanup seçeneği
            cleanup = input(f"\n🧹 Demo index'ini silmek ister misiniz? (y/N): ")
            if cleanup.lower() == 'y':
                self.cleanup_demo_data(index_name)
                
        except Exception as e:
            print(f"❌ Demo sırasında hata: {str(e)}")
            raise

if __name__ == "__main__":
    es_demo = ElasticsearchBasics()
    es_demo.run_all_demos()