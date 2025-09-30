"""
Elasticsearch Advanced CRUD Operations

Bu dosya Elasticsearch için gelişmiş CRUD operasyonları ve 
index management örnekleri içerir.
"""

from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timedelta
import json
import uuid
import random
from typing import List, Dict, Any, Optional
import time

class AdvancedElasticsearchCRUD:
    """
    Elasticsearch için gelişmiş CRUD operasyonları
    """
    
    def __init__(self, hosts=['localhost:9200'], **kwargs):
        """
        Elasticsearch client başlat
        
        Args:
            hosts: Elasticsearch host listesi
            **kwargs: Ek connection parametreleri
        """
        self.es = Elasticsearch(hosts, **kwargs)
        print(f"✅ Elasticsearch'e bağlanıldı: {hosts}")
        
        # Connection test
        try:
            info = self.es.info()
            print(f"📊 Cluster: {info['cluster_name']}, Version: {info['version']['number']}")
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
    
    def setup_product_index(self):
        """
        Product index'ini template ile oluştur
        """
        print("\n🏗️  Product Index Setup")
        print("-" * 40)
        
        # Index template
        template_config = {
            "index_patterns": ["products-*"],
            "priority": 100,
            "template": {
                "settings": {
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                    "refresh_interval": "30s",
                    "analysis": {
                        "analyzer": {
                            "product_search": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop", "stemmer"]
                            },
                            "product_ngram": {
                                "type": "custom",
                                "tokenizer": "ngram_tokenizer",
                                "filter": ["lowercase"]
                            }
                        },
                        "tokenizer": {
                            "ngram_tokenizer": {
                                "type": "ngram",
                                "min_gram": 2,
                                "max_gram": 3,
                                "token_chars": ["letter", "digit"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "name": {
                            "type": "text",
                            "analyzer": "product_search",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                },
                                "ngram": {
                                    "type": "text",
                                    "analyzer": "product_ngram"
                                },
                                "suggest": {
                                    "type": "completion"
                                }
                            }
                        },
                        "description": {
                            "type": "text",
                            "analyzer": "product_search"
                        },
                        "price": {
                            "type": "double"
                        },
                        "category": {
                            "type": "keyword"
                        },
                        "brand": {
                            "type": "keyword"
                        },
                        "tags": {
                            "type": "keyword"
                        },
                        "specifications": {
                            "type": "object",
                            "dynamic": True
                        },
                        "rating": {
                            "type": "float"
                        },
                        "review_count": {
                            "type": "integer"
                        },
                        "in_stock": {
                            "type": "boolean"
                        },
                        "created_at": {
                            "type": "date"
                        },
                        "updated_at": {
                            "type": "date"
                        },
                        "location": {
                            "type": "geo_point"
                        }
                    }
                }
            }
        }
        
        try:
            # Template oluştur
            self.es.indices.put_index_template(
                name="products_template",
                body=template_config
            )
            print("✅ Index template oluşturuldu")
            
            # Index oluştur
            index_name = "products-demo"
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name)
                print(f"✅ Index oluşturuldu: {index_name}")
            else:
                print(f"📋 Index zaten mevcut: {index_name}")
                
            return index_name
            
        except Exception as e:
            print(f"❌ Index setup hatası: {e}")
            return None
    
    def generate_sample_products(self, count=50):
        """
        Test için sample product verileri oluştur
        
        Args:
            count: Oluşturulacak product sayısı
        """
        categories = ["electronics", "clothing", "books", "home", "sports"]
        brands = ["Apple", "Samsung", "Nike", "Adidas", "Sony", "LG", "Dell", "HP"]
        
        products = []
        
        for i in range(count):
            category = random.choice(categories)
            brand = random.choice(brands)
            
            product = {
                "name": f"{brand} {category.title()} Product {i+1}",
                "description": f"High quality {category} product from {brand}. Perfect for daily use.",
                "price": round(random.uniform(10, 2000), 2),
                "category": category,
                "brand": brand,
                "tags": [category, brand.lower(), "popular"],
                "specifications": {
                    "weight": f"{random.uniform(0.1, 5.0):.1f}kg",
                    "color": random.choice(["black", "white", "red", "blue", "green"]),
                    "warranty": f"{random.randint(1, 3)} years"
                },
                "rating": round(random.uniform(1, 5), 1),
                "review_count": random.randint(0, 1000),
                "in_stock": random.choice([True, False]),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
                "updated_at": datetime.now().isoformat(),
                "location": {
                    "lat": round(random.uniform(36, 42), 4),  # Turkey coordinates
                    "lon": round(random.uniform(26, 45), 4)
                }
            }
            
            products.append(product)
        
        return products
    
    def demo_single_document_operations(self, index_name):
        """
        Tekil document operasyonları demo
        """
        print("\n📄 Single Document Operations")
        print("-" * 40)
        
        # 1. Document oluştur
        product = {
            "name": "iPhone 14 Pro",
            "description": "Latest iPhone with advanced camera system",
            "price": 999.99,
            "category": "electronics",
            "brand": "Apple",
            "tags": ["smartphone", "apple", "premium"],
            "specifications": {
                "storage": "128GB",
                "color": "Deep Purple",
                "display": "6.1 inch"
            },
            "rating": 4.8,
            "review_count": 250,
            "in_stock": True
        }
        
        doc_id = "iphone-14-pro"
        
        try:
            # Create
            result = self.es.index(
                index=index_name,
                id=doc_id,
                body={
                    **product,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                op_type='create'
            )
            print(f"✅ Document oluşturuldu: {doc_id} (version: {result['_version']})")
            
        except Exception as e:
            print(f"⚠️  Document zaten mevcut: {e}")
        
        # 2. Document getir
        try:
            doc = self.es.get(index=index_name, id=doc_id)
            print(f"📖 Document getirildi: {doc['_source']['name']}")
            print(f"   Fiyat: ${doc['_source']['price']}")
            print(f"   Stok: {'✅' if doc['_source']['in_stock'] else '❌'}")
            current_version = doc['_version']
            
        except Exception as e:
            print(f"❌ Document getirme hatası: {e}")
            return
        
        # 3. Document güncelle
        try:
            update_result = self.es.update(
                index=index_name,
                id=doc_id,
                body={
                    "doc": {
                        "price": 899.99,  # Fiyat indirimi
                        "on_sale": True,
                        "updated_at": datetime.now().isoformat()
                    }
                },
                version=current_version
            )
            print(f"✅ Document güncellendi: version {update_result['_version']}")
            
        except Exception as e:
            print(f"❌ Update hatası: {e}")
        
        # 4. Script ile güncelleme
        try:
            script_result = self.es.update(
                index=index_name,
                id=doc_id,
                body={
                    "script": {
                        "source": """
                        ctx._source.review_count += params.new_reviews;
                        ctx._source.rating = (ctx._source.rating * ctx._source.review_count + params.total_rating) / (ctx._source.review_count + params.new_reviews);
                        ctx._source.updated_at = params.timestamp;
                        """,
                        "params": {
                            "new_reviews": 25,
                            "total_rating": 120,  # 25 reviews with avg 4.8 rating
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                }
            )
            print(f"✅ Script ile güncellendi: version {script_result['_version']}")
            
        except Exception as e:
            print(f"❌ Script update hatası: {e}")
        
        # 5. Upsert operation
        try:
            upsert_result = self.es.update(
                index=index_name,
                id="samsung-galaxy-s23",
                body={
                    "doc": {
                        "price": 799.99,
                        "updated_at": datetime.now().isoformat()
                    },
                    "upsert": {
                        "name": "Samsung Galaxy S23",
                        "description": "Advanced Android smartphone",
                        "price": 799.99,
                        "category": "electronics",
                        "brand": "Samsung",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                }
            )
            print(f"✅ Upsert tamamlandı: {upsert_result['result']}")
            
        except Exception as e:
            print(f"❌ Upsert hatası: {e}")
    
    def demo_bulk_operations(self, index_name):
        """
        Bulk operasyon demo
        """
        print("\n📦 Bulk Operations")
        print("-" * 40)
        
        # Sample products oluştur
        products = self.generate_sample_products(20)
        
        # Bulk actions listesi hazırla
        bulk_actions = []
        
        for i, product in enumerate(products):
            # Action header
            action = {
                "index": {
                    "_index": index_name,
                    "_id": f"bulk-product-{i+1}"
                }
            }
            
            # Document body
            bulk_actions.append(action)
            bulk_actions.append(product)
        
        try:
            # Bulk indexing
            start_time = time.time()
            
            result = self.es.bulk(body=bulk_actions)
            
            end_time = time.time()
            
            # Sonuçları analiz et
            success_count = 0
            error_count = 0
            
            for item in result['items']:
                if 'index' in item:
                    if 'error' in item['index']:
                        error_count += 1
                    else:
                        success_count += 1
            
            print(f"✅ Bulk indexing tamamlandı:")
            print(f"   📊 Toplam: {len(products)} document")
            print(f"   ✅ Başarılı: {success_count}")
            print(f"   ❌ Hatalı: {error_count}")
            print(f"   ⏱️  Süre: {end_time - start_time:.2f} saniye")
            print(f"   🚀 Throughput: {success_count / (end_time - start_time):.0f} docs/sec")
            
        except Exception as e:
            print(f"❌ Bulk operations hatası: {e}")
    
    def demo_multi_get(self, index_name):
        """
        Multi-get operations demo
        """
        print("\n📚 Multi-Get Operations")
        print("-" * 40)
        
        # Multi-get request
        mget_body = {
            "docs": [
                {
                    "_index": index_name,
                    "_id": "iphone-14-pro"
                },
                {
                    "_index": index_name,
                    "_id": "samsung-galaxy-s23",
                    "_source": ["name", "price", "brand"]
                },
                {
                    "_index": index_name,
                    "_id": "bulk-product-1"
                },
                {
                    "_index": index_name,
                    "_id": "non-existent-product"
                }
            ]
        }
        
        try:
            result = self.es.mget(body=mget_body)
            
            print(f"📖 Multi-get sonuçları:")
            
            for doc in result['docs']:
                if doc['found']:
                    source = doc['_source']
                    print(f"   ✅ {doc['_id']}: {source.get('name', 'N/A')} - ${source.get('price', 'N/A')}")
                else:
                    print(f"   ❌ {doc['_id']}: Bulunamadı")
                    
        except Exception as e:
            print(f"❌ Multi-get hatası: {e}")
    
    def demo_update_by_query(self, index_name):
        """
        Update by query demo
        """
        print("\n🔄 Update by Query")
        print("-" * 40)
        
        # Tüm Apple ürünlerinin fiyatına %10 indirim uygula
        try:
            result = self.es.update_by_query(
                index=index_name,
                body={
                    "query": {
                        "term": {
                            "brand": "Apple"
                        }
                    },
                    "script": {
                        "source": """
                        ctx._source.price = Math.round(ctx._source.price * 0.9 * 100.0) / 100.0;
                        ctx._source.on_sale = true;
                        ctx._source.discount_percent = 10;
                        ctx._source.updated_at = params.timestamp;
                        """,
                        "params": {
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                },
                wait_for_completion=True
            )
            
            print(f"✅ Update by query tamamlandı:")
            print(f"   📊 Güncellenen document sayısı: {result['updated']}")
            print(f"   ⏱️  Süre: {result['took']}ms")
            
        except Exception as e:
            print(f"❌ Update by query hatası: {e}")
    
    def demo_delete_operations(self, index_name):
        """
        Delete operations demo
        """
        print("\n🗑️  Delete Operations")
        print("-" * 40)
        
        # Single document delete
        try:
            result = self.es.delete(
                index=index_name,
                id="bulk-product-20"  # Son product'ı sil
            )
            print(f"✅ Document silindi: bulk-product-20")
            
        except Exception as e:
            print(f"⚠️  Delete hatası: {e}")
        
        # Delete by query - stokta olmayan ürünleri sil
        try:
            result = self.es.delete_by_query(
                index=index_name,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"in_stock": False}},
                                {"range": {"price": {"lt": 50}}}  # Düşük fiyatlı ve stokta olmayan
                            ]
                        }
                    }
                },
                wait_for_completion=True
            )
            
            print(f"✅ Delete by query tamamlandı:")
            print(f"   📊 Silinen document sayısı: {result['deleted']}")
            print(f"   ⏱️  Süre: {result['took']}ms")
            
        except Exception as e:
            print(f"❌ Delete by query hatası: {e}")
    
    def demo_advanced_search(self, index_name):
        """
        Advanced search operations demo
        """
        print("\n🔍 Advanced Search Operations")
        print("-" * 40)
        
        # 1. Complex bool query
        search_body = {
            "size": 10,
            "query": {
                "bool": {
                    "must": [
                        {"range": {"price": {"gte": 100, "lte": 1000}}}
                    ],
                    "should": [
                        {"match": {"description": "high quality"}},
                        {"term": {"brand": "Apple"}}
                    ],
                    "filter": [
                        {"term": {"in_stock": True}},
                        {"terms": {"category": ["electronics", "clothing"]}}
                    ]
                }
            },
            "sort": [
                {"rating": {"order": "desc"}},
                {"price": {"order": "asc"}}
            ],
            "_source": ["name", "price", "brand", "rating"]
        }
        
        try:
            result = self.es.search(index=index_name, body=search_body)
            
            print(f"🔍 Search sonuçları ({result['hits']['total']['value']} toplam):")
            
            for hit in result['hits']['hits']:
                source = hit['_source']
                score = hit['_score']
                print(f"   📱 {source['name']} - ${source['price']} (Score: {score:.2f})")
                print(f"      Brand: {source['brand']}, Rating: {source['rating']}")
                
        except Exception as e:
            print(f"❌ Search hatası: {e}")
    
    def demo_aggregations(self, index_name):
        """
        Aggregation demo
        """
        print("\n📊 Aggregations")
        print("-" * 40)
        
        agg_body = {
            "size": 0,  # Sadece aggregation sonuçları
            "aggs": {
                "categories": {
                    "terms": {
                        "field": "category",
                        "size": 10
                    },
                    "aggs": {
                        "avg_price": {
                            "avg": {
                                "field": "price"
                            }
                        },
                        "price_stats": {
                            "stats": {
                                "field": "price"
                            }
                        }
                    }
                },
                "price_histogram": {
                    "histogram": {
                        "field": "price",
                        "interval": 200
                    }
                },
                "rating_ranges": {
                    "range": {
                        "field": "rating",
                        "ranges": [
                            {"to": 2},
                            {"from": 2, "to": 3},
                            {"from": 3, "to": 4},
                            {"from": 4}
                        ]
                    }
                }
            }
        }
        
        try:
            result = self.es.search(index=index_name, body=agg_body)
            
            # Category aggregation
            print("📂 Kategori bazlı istatistikler:")
            for bucket in result['aggregations']['categories']['buckets']:
                category = bucket['key']
                count = bucket['doc_count']
                avg_price = bucket['avg_price']['value']
                
                print(f"   {category}: {count} ürün, Ortalama fiyat: ${avg_price:.2f}")
            
            # Price histogram
            print("\n💰 Fiyat dağılımı:")
            for bucket in result['aggregations']['price_histogram']['buckets']:
                price_range = f"${bucket['key']}-${bucket['key'] + 200}"
                count = bucket['doc_count']
                print(f"   {price_range}: {count} ürün")
            
            # Rating ranges
            print("\n⭐ Rating dağılımı:")
            rating_labels = ["😞 Poor (0-2)", "😐 Fair (2-3)", "😊 Good (3-4)", "🌟 Excellent (4+)"]
            for i, bucket in enumerate(result['aggregations']['rating_ranges']['buckets']):
                count = bucket['doc_count']
                print(f"   {rating_labels[i]}: {count} ürün")
                
        except Exception as e:
            print(f"❌ Aggregation hatası: {e}")
    
    def get_index_stats(self, index_name):
        """
        Index istatistiklerini göster
        """
        print(f"\n📊 Index İstatistikleri: {index_name}")
        print("-" * 40)
        
        try:
            # Index stats
            stats = self.es.indices.stats(index=index_name)
            index_stats = stats['indices'][index_name]
            
            print(f"📄 Document sayısı: {index_stats['total']['docs']['count']}")
            print(f"🗑️  Silinen document: {index_stats['total']['docs']['deleted']}")
            print(f"💾 Store boyutu: {index_stats['total']['store']['size_in_bytes'] / 1024 / 1024:.2f} MB")
            
            # Index mapping
            mapping = self.es.indices.get_mapping(index=index_name)
            properties = mapping[index_name]['mappings']['properties']
            print(f"🗂️  Field sayısı: {len(properties)}")
            
            # Index settings
            settings = self.es.indices.get_settings(index=index_name)
            index_settings = settings[index_name]['settings']['index']
            print(f"🔧 Shard sayısı: {index_settings['number_of_shards']}")
            print(f"📋 Replica sayısı: {index_settings['number_of_replicas']}")
            
        except Exception as e:
            print(f"❌ Stats alma hatası: {e}")

def main():
    """
    Ana demo fonksiyonu
    """
    print("🔧 Elasticsearch Advanced CRUD Operations Demo")
    print("=" * 60)
    
    # Client oluştur
    crud = AdvancedElasticsearchCRUD()
    
    # Index setup
    index_name = crud.setup_product_index()
    if not index_name:
        print("❌ Index setup başarısız, demo sonlandırılıyor")
        return
    
    # Demo scenarios
    scenarios = [
        ("Single Document Operations", crud.demo_single_document_operations),
        ("Bulk Operations", crud.demo_bulk_operations),
        ("Multi-Get Operations", crud.demo_multi_get),
        ("Update by Query", crud.demo_update_by_query),
        ("Advanced Search", crud.demo_advanced_search),
        ("Aggregations", crud.demo_aggregations),
        ("Delete Operations", crud.demo_delete_operations)
    ]
    
    # Tüm scenario'ları çalıştır
    for scenario_name, scenario_func in scenarios:
        try:
            scenario_func(index_name)
            time.sleep(1)  # Elasticsearch'in refresh olması için
        except Exception as e:
            print(f"❌ {scenario_name} hatası: {e}")
    
    # Final stats
    crud.get_index_stats(index_name)
    
    print("\n✅ Demo tamamlandı!")
    print("💡 Kibana'da sonuçları incelemek için: http://localhost:5601")

if __name__ == "__main__":
    main()