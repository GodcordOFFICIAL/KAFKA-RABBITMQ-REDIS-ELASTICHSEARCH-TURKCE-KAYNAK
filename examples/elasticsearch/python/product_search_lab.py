# examples/elasticsearch/python/product_search_lab.py
from elasticsearch import Elasticsearch
import json
from datetime import datetime
from typing import Dict, List, Optional
import random

class ProductSearchSystem:
    def __init__(self):
        self.es = Elasticsearch(
            [{'host': 'localhost', 'port': 9200, 'scheme': 'http'}],
            verify_certs=False,
            ssl_show_warn=False
        )
        
        self.index_name = "ecommerce-products"
        print("🛒 E-ticaret Ürün Arama Sistemi başlatıldı")
        
    def setup_product_index(self):
        """Ürün index'ini kur"""
        print("\n📚 Ürün index'i kuruluyor...")
        
        # Eski index'i sil
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
            print(f"🗑️ Eski index silindi: {self.index_name}")
        
        # Product mapping
        index_body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "product_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "stop",
                                "stemmer"
                            ]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "product_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "product_analyzer"
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "brand": {
                        "type": "keyword"
                    },
                    "price": {
                        "type": "float"
                    },
                    "original_price": {
                        "type": "float"
                    },
                    "discount_percentage": {
                        "type": "float"
                    },
                    "rating": {
                        "type": "float"
                    },
                    "review_count": {
                        "type": "integer"
                    },
                    "stock_quantity": {
                        "type": "integer"
                    },
                    "tags": {
                        "type": "keyword"
                    },
                    "created_at": {
                        "type": "date"
                    },
                    "is_featured": {
                        "type": "boolean"
                    },
                    "is_available": {
                        "type": "boolean"
                    },
                    "colors": {
                        "type": "keyword"
                    },
                    "sizes": {
                        "type": "keyword"
                    }
                }
            }
        }
        
        self.es.indices.create(index=self.index_name, body=index_body)
        print(f"✅ Index oluşturuldu: {self.index_name}")
    
    def load_sample_products(self):
        """Örnek ürünleri yükle"""
        print("\n📦 Örnek ürünler yükleniyor...")
        
        products = [
            {
                "name": "iPhone 15 Pro Max",
                "description": "Apple'ın en gelişmiş akıllı telefonu. A17 Pro çip, 48MP kamera sistemi ve titanium tasarım.",
                "category": "electronics",
                "brand": "Apple",
                "price": 1299.99,
                "original_price": 1399.99,
                "discount_percentage": 7.14,
                "rating": 4.8,
                "review_count": 1250,
                "stock_quantity": 45,
                "tags": ["smartphone", "premium", "camera", "5g"],
                "is_featured": True,
                "is_available": True,
                "colors": ["black", "white", "blue", "natural"],
                "sizes": ["128GB", "256GB", "512GB", "1TB"]
            },
            {
                "name": "Samsung Galaxy S24 Ultra",
                "description": "Samsung'un amiral gemisi telefonu. S Pen desteği, gelişmiş kamera sistemi ve büyük ekran.",
                "category": "electronics",
                "brand": "Samsung",
                "price": 1199.99,
                "original_price": 1299.99,
                "discount_percentage": 7.69,
                "rating": 4.7,
                "review_count": 980,
                "stock_quantity": 32,
                "tags": ["smartphone", "stylus", "camera", "5g"],
                "is_featured": True,
                "is_available": True,
                "colors": ["black", "gray", "violet"],
                "sizes": ["256GB", "512GB", "1TB"]
            },
            {
                "name": "MacBook Pro 16-inch M3",
                "description": "Apple M3 çipli MacBook Pro. Profesyonel performans ve uzun pil ömrü.",
                "category": "computers",
                "brand": "Apple",
                "price": 2499.99,
                "original_price": 2499.99,
                "discount_percentage": 0,
                "rating": 4.9,
                "review_count": 756,
                "stock_quantity": 18,
                "tags": ["laptop", "professional", "m3", "retina"],
                "is_featured": True,
                "is_available": True,
                "colors": ["silver", "space_gray"],
                "sizes": ["16GB/512GB", "32GB/1TB", "64GB/2TB"]
            },
            {
                "name": "Nike Air Max 270",
                "description": "Konforlu ve şık spor ayakkabı. Air Max yastıklama teknolojisi ile tüm gün konfor.",
                "category": "shoes",
                "brand": "Nike",
                "price": 129.99,
                "original_price": 159.99,
                "discount_percentage": 18.75,
                "rating": 4.5,
                "review_count": 2340,
                "stock_quantity": 120,
                "tags": ["sneakers", "air_max", "comfort", "casual"],
                "is_featured": False,
                "is_available": True,
                "colors": ["white", "black", "red", "blue"],
                "sizes": ["38", "39", "40", "41", "42", "43", "44", "45"]
            },
            {
                "name": "Sony WH-1000XM5 Kulaklık",
                "description": "Sektörün en iyi gürültü önleme teknolojisi ile kablosuz kulaklık.",
                "category": "electronics",
                "brand": "Sony",
                "price": 349.99,
                "original_price": 399.99,
                "discount_percentage": 12.5,
                "rating": 4.6,
                "review_count": 1580,
                "stock_quantity": 67,
                "tags": ["headphones", "wireless", "noise_cancelling", "premium"],
                "is_featured": False,
                "is_available": True,
                "colors": ["black", "silver"],
                "sizes": ["one_size"]
            },
            {
                "name": "Levi's 501 Original Jeans",
                "description": "Klasik straight fit denim pantolon. %100 pamuk, vintage görünüm.",
                "category": "clothing",
                "brand": "Levi's",
                "price": 89.99,
                "original_price": 109.99,
                "discount_percentage": 18.18,
                "rating": 4.3,
                "review_count": 3450,
                "stock_quantity": 200,
                "tags": ["jeans", "denim", "classic", "cotton"],
                "is_featured": False,
                "is_available": True,
                "colors": ["blue", "black", "gray"],
                "sizes": ["28", "30", "32", "34", "36", "38", "40"]
            },
            {
                "name": "KitchenAid Stand Mixer",
                "description": "Profesyonel mutfak mikseri. 10 hız ayarı ve çeşitli aksesuarlar.",
                "category": "home",
                "brand": "KitchenAid",
                "price": 449.99,
                "original_price": 549.99,
                "discount_percentage": 18.18,
                "rating": 4.8,
                "review_count": 890,
                "stock_quantity": 25,
                "tags": ["kitchen", "mixer", "baking", "professional"],
                "is_featured": True,
                "is_available": True,
                "colors": ["red", "white", "black", "blue"],
                "sizes": ["5qt", "6qt", "7qt"]
            },
            {
                "name": "Dyson V15 Detect Vacuum",
                "description": "Lazer teknolojisi ile toz algılama özellikli kablosuz elektrikli süpürge.",
                "category": "home",
                "brand": "Dyson",
                "price": 649.99,
                "original_price": 749.99,
                "discount_percentage": 13.33,
                "rating": 4.7,
                "review_count": 1230,
                "stock_quantity": 34,
                "tags": ["vacuum", "cordless", "laser", "pet_hair"],
                "is_featured": True,
                "is_available": True,
                "colors": ["yellow", "purple"],
                "sizes": ["standard"]
            }
        ]
        
        # Bulk insert
        bulk_body = []
        for i, product in enumerate(products, 1):
            product['created_at'] = datetime.now().isoformat()
            bulk_body.extend([
                {"index": {"_index": self.index_name, "_id": f"prod_{i:03d}"}},
                product
            ])
        
        result = self.es.bulk(body=bulk_body)
        successful = sum(1 for item in result['items'] if item['index']['status'] == 201)
        print(f"✅ {successful} ürün eklendi")
        
        # Index refresh
        self.es.indices.refresh(index=self.index_name)
    
    def search_products(self, query: str, filters: Dict = None, sort_by: str = "relevance", size: int = 10):
        """Ürün arama"""
        search_body = {
            "size": size,
            "query": {},
            "highlight": {
                "fields": {
                    "name": {},
                    "description": {}
                }
            }
        }
        
        # Ana query
        if query:
            search_body["query"] = {
                "multi_match": {
                    "query": query,
                    "fields": ["name^2", "description", "brand", "tags"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            }
        else:
            search_body["query"] = {"match_all": {}}
        
        # Filters uygula
        if filters:
            bool_query = {
                "bool": {
                    "must": [search_body["query"]]
                }
            }
            
            if filters.get('category'):
                bool_query["bool"]["filter"] = [
                    {"term": {"category": filters['category']}}
                ]
            
            if filters.get('brand'):
                if "filter" not in bool_query["bool"]:
                    bool_query["bool"]["filter"] = []
                bool_query["bool"]["filter"].append(
                    {"term": {"brand": filters['brand']}}
                )
            
            if filters.get('price_min') or filters.get('price_max'):
                price_range = {}
                if filters.get('price_min'):
                    price_range["gte"] = filters['price_min']
                if filters.get('price_max'):
                    price_range["lte"] = filters['price_max']
                
                if "filter" not in bool_query["bool"]:
                    bool_query["bool"]["filter"] = []
                bool_query["bool"]["filter"].append(
                    {"range": {"price": price_range}}
                )
            
            if filters.get('min_rating'):
                if "filter" not in bool_query["bool"]:
                    bool_query["bool"]["filter"] = []
                bool_query["bool"]["filter"].append(
                    {"range": {"rating": {"gte": filters['min_rating']}}}
                )
            
            if filters.get('in_stock_only'):
                if "filter" not in bool_query["bool"]:
                    bool_query["bool"]["filter"] = []
                bool_query["bool"]["filter"].extend([
                    {"term": {"is_available": True}},
                    {"range": {"stock_quantity": {"gt": 0}}}
                ])
            
            search_body["query"] = bool_query
        
        # Sorting
        if sort_by == "price_asc":
            search_body["sort"] = [{"price": {"order": "asc"}}]
        elif sort_by == "price_desc":
            search_body["sort"] = [{"price": {"order": "desc"}}]
        elif sort_by == "rating":
            search_body["sort"] = [{"rating": {"order": "desc"}}]
        elif sort_by == "popularity":
            search_body["sort"] = [{"review_count": {"order": "desc"}}]
        elif sort_by == "newest":
            search_body["sort"] = [{"created_at": {"order": "desc"}}]
        # relevance için sort eklemeyelim (default scoring)
        
        return self.es.search(index=self.index_name, body=search_body)
    
    def get_search_suggestions(self, query: str, size: int = 5):
        """Arama önerileri"""
        search_body = {
            "size": 0,
            "suggest": {
                "product_suggestions": {
                    "text": query,
                    "term": {
                        "field": "name",
                        "size": size
                    }
                }
            }
        }
        
        return self.es.search(index=self.index_name, body=search_body)
    
    def get_product_analytics(self):
        """Ürün analitikleri"""
        agg_body = {
            "size": 0,
            "aggs": {
                "categories": {
                    "terms": {"field": "category"}
                },
                "brands": {
                    "terms": {"field": "brand", "size": 10}
                },
                "price_ranges": {
                    "range": {
                        "field": "price",
                        "ranges": [
                            {"to": 100},
                            {"from": 100, "to": 500},
                            {"from": 500, "to": 1000},
                            {"from": 1000}
                        ]
                    }
                },
                "avg_rating": {
                    "avg": {"field": "rating"}
                },
                "total_stock": {
                    "sum": {"field": "stock_quantity"}
                }
            }
        }
        
        return self.es.search(index=self.index_name, body=agg_body)
    
    def run_search_demo(self):
        """Arama demo'su çalıştır"""
        print("\n🔍 ÜRÜN ARAMA DEMO'SU")
        print("=" * 50)
        
        # 1. Basit text arama
        print("\n📱 'iPhone' araması:")
        result = self.search_products("iPhone")
        self.print_search_results(result)
        
        # 2. Category filter ile arama
        print("\n👔 Electronics kategorisinde 'wireless' araması:")
        result = self.search_products(
            "wireless", 
            filters={"category": "electronics"}
        )
        self.print_search_results(result)
        
        # 3. Fiyat aralığı ile arama
        print("\n💰 100-500 TL arası ürünler:")
        result = self.search_products(
            "", 
            filters={"price_min": 100, "price_max": 500},
            sort_by="price_asc"
        )
        self.print_search_results(result)
        
        # 4. Yüksek puanlı ürünler
        print("\n⭐ 4.5+ puan alan ürünler (popülerlik sırasına göre):")
        result = self.search_products(
            "",
            filters={"min_rating": 4.5},
            sort_by="popularity"
        )
        self.print_search_results(result)
        
        # 5. Analytics
        print("\n📊 ÜRÜN ANALİTİKLERİ:")
        analytics = self.get_product_analytics()
        self.print_analytics(analytics)
    
    def print_search_results(self, result):
        """Arama sonuçlarını yazdır"""
        hits = result['hits']
        total = hits['total']['value']
        
        if total == 0:
            print("   ❌ Sonuç bulunamadı")
            return
        
        print(f"   📊 {total} sonuç bulundu")
        
        for hit in hits['hits'][:5]:  # İlk 5 sonuç
            source = hit['_source']
            score = hit['_score']
            
            # Discount badge
            discount_badge = ""
            if source['discount_percentage'] > 0:
                discount_badge = f" 🏷️ %{source['discount_percentage']:.0f} indirim"
            
            # Stock status
            stock_status = "✅" if source['is_available'] and source['stock_quantity'] > 0 else "❌"
            
            print(f"   {stock_status} {source['name']}")
            print(f"      💰 {source['price']:.2f} TL{discount_badge}")
            print(f"      ⭐ {source['rating']}/5 ({source['review_count']} değerlendirme)")
            print(f"      📦 Stok: {source['stock_quantity']}")
            print(f"      🏷️ {source['brand']} - {source['category']}")
            
            # Highlight göster
            if 'highlight' in hit:
                for field, highlights in hit['highlight'].items():
                    print(f"      💡 {field}: {highlights[0]}")
            
            print()
    
    def print_analytics(self, analytics):
        """Analitik sonuçlarını yazdır"""
        aggs = analytics['aggregations']
        
        print("   📈 Kategorilere göre dağılım:")
        for bucket in aggs['categories']['buckets']:
            print(f"      {bucket['key']}: {bucket['doc_count']} ürün")
        
        print("\n   🏢 Markalara göre dağılım:")
        for bucket in aggs['brands']['buckets']:
            print(f"      {bucket['key']}: {bucket['doc_count']} ürün")
        
        print("\n   💰 Fiyat aralıkları:")
        for bucket in aggs['price_ranges']['buckets']:
            key = bucket['key']
            if 'from' in bucket and 'to' in bucket:
                range_str = f"{bucket['from']:.0f}-{bucket['to']:.0f} TL"
            elif 'from' in bucket:
                range_str = f"{bucket['from']:.0f}+ TL"
            else:
                range_str = f"0-{bucket['to']:.0f} TL"
            print(f"      {range_str}: {bucket['doc_count']} ürün")
        
        print(f"\n   ⭐ Ortalama rating: {aggs['avg_rating']['value']:.2f}")
        print(f"   📦 Toplam stok: {aggs['total_stock']['value']:.0f} adet")

if __name__ == "__main__":
    system = ProductSearchSystem()
    
    try:
        # Setup
        system.setup_product_index()
        system.load_sample_products()
        
        # Demo
        system.run_search_demo()
        
        print("\n✅ E-ticaret ürün arama sistemi demo'su tamamlandı!")
        
    except Exception as e:
        print(f"❌ Demo sırasında hata: {str(e)}")
        raise