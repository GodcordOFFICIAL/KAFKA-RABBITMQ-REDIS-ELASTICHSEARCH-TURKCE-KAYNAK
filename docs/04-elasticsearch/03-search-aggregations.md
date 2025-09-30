# Elasticsearch Complex Search Queries ve Aggregations

## 📋 Özet

Bu bölümde Elasticsearch'in güçlü query DSL'ini ve aggregation framework'ünü derinlemesine öğreneceksiniz. Complex search scenarios, real-time analytics ve data mining için gerekli tüm teknikleri kapsamlı olarak ele alacağız.

## 🎯 Learning Objectives

Bu bölümü tamamladığında:

- ✅ Query DSL'in tüm query types'larını kullanabileceksin
- ✅ Bool queries ile complex search logic yazabileceksin
- ✅ Full-text search ve filtering'i optimize edebileceksin
- ✅ Aggregations ile real-time analytics yapabileceksin
- ✅ Nested ve parent-child relationships query'leyebileceksin
- ✅ Geo-spatial search implementasyonu yapabileceksin
- ✅ Search performance optimization uygulayabileceksin

## 📋 Prerequisites

- Elasticsearch CRUD operations bilgisi
- JSON formatı ve REST API kullanımı
- SQL aggregate functions anlayışı
- Basic statistics kavramları

## 🔍 Query DSL Deep Dive

### Query Context vs Filter Context

**Query Context**: Relevance scoring ile birlikte
**Filter Context**: Sadece match/no-match, caching mümkün

```json
{
  "query": {
    "bool": {
      "must": [
        // Query context - scoring yapılır
        {
          "match": {
            "title": "elasticsearch guide"
          }
        }
      ],
      "filter": [
        // Filter context - sadece filtering, cache'lenir
        {
          "range": {
            "price": {
              "gte": 100,
              "lte": 1000
            }
          }
        }
      ]
    }
  }
}
```

### Full-Text Search Queries

#### 1. Match Query

```json
// Basic match
{
  "query": {
    "match": {
      "description": "high quality laptop"
    }
  }
}

// Match with operator
{
  "query": {
    "match": {
      "description": {
        "query": "high quality laptop",
        "operator": "and",
        "minimum_should_match": "75%"
      }
    }
  }
}

// Match phrase
{
  "query": {
    "match_phrase": {
      "description": {
        "query": "high quality",
        "slop": 2
      }
    }
  }
}
```

#### 2. Multi-Match Query

```json
{
  "query": {
    "multi_match": {
      "query": "elasticsearch tutorial",
      "fields": ["title^2", "description", "tags"],
      "type": "best_fields",
      "tie_breaker": 0.3
    }
  }
}
```

#### 3. Query String ve Simple Query String

```json
// Query string (advanced)
{
  "query": {
    "query_string": {
      "query": "title:(elasticsearch OR kibana) AND status:published",
      "default_field": "description"
    }
  }
}

// Simple query string (user-friendly)
{
  "query": {
    "simple_query_string": {
      "query": "elasticsearch + tutorial -beginner",
      "fields": ["title", "description"],
      "default_operator": "AND"
    }
  }
}
```

### Term-Level Queries

```json
// Term query (exact match)
{
  "query": {
    "term": {
      "status": "published"
    }
  }
}

// Terms query (multiple values)
{
  "query": {
    "terms": {
      "category": ["electronics", "computers", "software"]
    }
  }
}

// Range query
{
  "query": {
    "range": {
      "price": {
        "gte": 100,
        "lte": 1000
      }
    }
  }
}

// Exists query
{
  "query": {
    "exists": {
      "field": "description"
    }
  }
}

// Wildcard query
{
  "query": {
    "wildcard": {
      "title": "elastic*"
    }
  }
}

// Fuzzy query
{
  "query": {
    "fuzzy": {
      "title": {
        "value": "elasticsarch",
        "fuzziness": "AUTO"
      }
    }
  }
}
```

### Bool Query - Complex Logic

```json
{
  "query": {
    "bool": {
      "must": [
        // AND logic - must match
        {
          "match": {
            "description": "elasticsearch"
          }
        }
      ],
      "should": [
        // OR logic - boost scoring
        {
          "match": {
            "title": "tutorial"
          }
        },
        {
          "match": {
            "tags": "beginners"
          }
        }
      ],
      "must_not": [
        // NOT logic - must not match
        {
          "term": {
            "status": "draft"
          }
        }
      ],
      "filter": [
        // Filter context - no scoring
        {
          "range": {
            "published_date": {
              "gte": "2023-01-01"
            }
          }
        },
        {
          "terms": {
            "category": ["tutorial", "guide"]
          }
        }
      ],
      "minimum_should_match": 1
    }
  }
}
```

## 💻 Python ile Complex Search Implementation

```python
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional

class ElasticsearchQueryBuilder:
    """
    Elasticsearch complex query builder
    """

    def __init__(self, hosts=['localhost:9200'], **kwargs):
        """
        Elasticsearch client başlat
        """
        self.es = Elasticsearch(hosts, **kwargs)
        print(f"✅ Elasticsearch Query Builder başlatıldı")

    def build_product_search_query(self,
                                 search_text: str = None,
                                 categories: List[str] = None,
                                 price_range: Dict = None,
                                 rating_min: float = None,
                                 in_stock: bool = None,
                                 brands: List[str] = None,
                                 sort_by: str = "_score",
                                 sort_order: str = "desc") -> Dict:
        """
        E-ticaret ürün arama query'si oluştur

        Args:
            search_text: Arama metni
            categories: Kategori filtreleri
            price_range: {"min": 100, "max": 1000}
            rating_min: Minimum rating
            in_stock: Stok durumu
            brands: Marka filtreleri
            sort_by: Sıralama field'ı
            sort_order: Sıralama yönü
        """
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "should": [],
                    "filter": [],
                    "must_not": []
                }
            },
            "sort": [],
            "_source": ["name", "description", "price", "category", "brand", "rating", "in_stock"],
            "highlight": {
                "fields": {
                    "name": {},
                    "description": {}
                }
            }
        }

        # Full-text search
        if search_text:
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": search_text,
                    "fields": [
                        "name^3",           # Name'e 3x boost
                        "description^2",    # Description'a 2x boost
                        "brand^1.5",        # Brand'e 1.5x boost
                        "category",
                        "tags"
                    ],
                    "type": "best_fields",
                    "tie_breaker": 0.3,
                    "fuzziness": "AUTO"
                }
            })

            # Exact phrase bonus
            query["query"]["bool"]["should"].append({
                "match_phrase": {
                    "name": {
                        "query": search_text,
                        "boost": 2
                    }
                }
            })

        # Category filter
        if categories:
            query["query"]["bool"]["filter"].append({
                "terms": {
                    "category": categories
                }
            })

        # Price range filter
        if price_range:
            range_filter = {"range": {"price": {}}}
            if "min" in price_range:
                range_filter["range"]["price"]["gte"] = price_range["min"]
            if "max" in price_range:
                range_filter["range"]["price"]["lte"] = price_range["max"]
            query["query"]["bool"]["filter"].append(range_filter)

        # Rating filter
        if rating_min:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "rating": {
                        "gte": rating_min
                    }
                }
            })

        # Stock filter
        if in_stock is not None:
            query["query"]["bool"]["filter"].append({
                "term": {
                    "in_stock": in_stock
                }
            })

        # Brand filter
        if brands:
            query["query"]["bool"]["filter"].append({
                "terms": {
                    "brand": brands
                }
            })

        # Sorting
        if sort_by == "price":
            query["sort"].append({"price": {"order": sort_order}})
        elif sort_by == "rating":
            query["sort"].append({"rating": {"order": sort_order}})
        elif sort_by == "popularity":
            query["sort"].append({"review_count": {"order": sort_order}})
        else:
            query["sort"].append({sort_by: {"order": sort_order}})

        # Fallback sorting
        query["sort"].append({"_id": {"order": "asc"}})

        return query

    def search_products(self, index: str = "products", **search_params) -> Dict:
        """
        Ürün arama yap
        """
        query = self.build_product_search_query(**search_params)

        try:
            result = self.es.search(
                index=index,
                body=query,
                size=search_params.get('size', 20),
                from_=search_params.get('from_', 0)
            )

            # Sonuçları format et
            formatted_results = {
                'total': result['hits']['total']['value'],
                'took': result['took'],
                'products': []
            }

            for hit in result['hits']['hits']:
                product = hit['_source']
                product['_score'] = hit['_score']
                product['_id'] = hit['_id']

                # Highlight'ları ekle
                if 'highlight' in hit:
                    product['_highlight'] = hit['highlight']

                formatted_results['products'].append(product)

            return formatted_results

        except Exception as e:
            print(f"❌ Search hatası: {e}")
            return {'total': 0, 'products': [], 'error': str(e)}

    def search_suggestions(self, index: str, field: str, prefix: str, size: int = 5) -> List[str]:
        """
        Auto-complete önerileri
        """
        query = {
            "suggest": {
                "product_suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": field,
                        "size": size,
                        "skip_duplicates": True
                    }
                }
            }
        }

        try:
            result = self.es.search(index=index, body=query)
            suggestions = []

            for suggestion in result['suggest']['product_suggest'][0]['options']:
                suggestions.append(suggestion['text'])

            return suggestions

        except Exception as e:
            print(f"❌ Suggestion hatası: {e}")
            return []

    def build_analytics_query(self,
                            index: str,
                            date_range: Dict = None,
                            group_by: str = None,
                            metrics: List[str] = None) -> Dict:
        """
        Analytics query oluştur

        Args:
            date_range: {"from": "2023-01-01", "to": "2023-12-31"}
            group_by: Gruplandırma field'ı
            metrics: ["avg_price", "total_sales", "count"]
        """
        query = {
            "size": 0,  # Sadece aggregation sonuçları
            "query": {
                "bool": {
                    "filter": []
                }
            },
            "aggs": {}
        }

        # Date range filter
        if date_range:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "created_at": {
                        "gte": date_range.get("from"),
                        "lte": date_range.get("to")
                    }
                }
            })

        # Group by aggregation
        if group_by:
            query["aggs"]["group_by"] = {
                "terms": {
                    "field": group_by,
                    "size": 50
                },
                "aggs": {}
            }

            # Metrics aggregations
            if metrics:
                agg_target = query["aggs"]["group_by"]["aggs"]

                for metric in metrics:
                    if metric == "avg_price":
                        agg_target["avg_price"] = {
                            "avg": {
                                "field": "price"
                            }
                        }
                    elif metric == "total_sales":
                        agg_target["total_sales"] = {
                            "sum": {
                                "field": "sales_amount"
                            }
                        }
                    elif metric == "count":
                        # Terms aggregation otomatik olarak doc_count verir
                        pass
                    elif metric == "max_price":
                        agg_target["max_price"] = {
                            "max": {
                                "field": "price"
                            }
                        }
                    elif metric == "min_price":
                        agg_target["min_price"] = {
                            "min": {
                                "field": "price"
                            }
                        }

        return query

class ElasticsearchAdvancedQueries:
    """
    Advanced Elasticsearch query examples
    """

    def __init__(self, hosts=['localhost:9200'], **kwargs):
        self.es = Elasticsearch(hosts, **kwargs)
        self.query_builder = ElasticsearchQueryBuilder(hosts, **kwargs)

    def demo_complex_product_search(self, index: str = "products"):
        """
        Complex product search demo
        """
        print("🔍 Complex Product Search Demo")
        print("=" * 50)

        # Test scenarios
        search_scenarios = [
            {
                "name": "Basic Text Search",
                "params": {
                    "search_text": "laptop gaming",
                    "size": 5
                }
            },
            {
                "name": "Filtered Search",
                "params": {
                    "search_text": "smartphone",
                    "categories": ["electronics"],
                    "price_range": {"min": 200, "max": 800},
                    "rating_min": 4.0,
                    "in_stock": True,
                    "size": 5
                }
            },
            {
                "name": "Brand & Price Search",
                "params": {
                    "brands": ["Apple", "Samsung"],
                    "price_range": {"min": 500},
                    "sort_by": "price",
                    "sort_order": "asc",
                    "size": 5
                }
            },
            {
                "name": "High-Rating Products",
                "params": {
                    "rating_min": 4.5,
                    "sort_by": "rating",
                    "sort_order": "desc",
                    "size": 3
                }
            }
        ]

        for scenario in search_scenarios:
            print(f"\n📋 {scenario['name']}:")
            print(f"   Parameters: {scenario['params']}")

            results = self.query_builder.search_products(index, **scenario['params'])

            if 'error' in results:
                print(f"   ❌ Error: {results['error']}")
                continue

            print(f"   📊 Total results: {results['total']} (took: {results['took']}ms)")

            for i, product in enumerate(results['products'][:3], 1):
                print(f"   {i}. {product['name']} - ${product['price']}")
                print(f"      Rating: {product.get('rating', 'N/A')}, Stock: {'✅' if product.get('in_stock') else '❌'}")

                # Highlight göster
                if '_highlight' in product:
                    for field, highlights in product['_highlight'].items():
                        print(f"      💡 {field}: {highlights[0]}")

    def demo_nested_queries(self, index: str = "products"):
        """
        Nested objects query demo
        """
        print("\n🏗️  Nested Query Demo")
        print("=" * 30)

        # Nested query for product reviews
        nested_query = {
            "query": {
                "nested": {
                    "path": "reviews",
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "range": {
                                        "reviews.rating": {
                                            "gte": 4
                                        }
                                    }
                                },
                                {
                                    "match": {
                                        "reviews.comment": "excellent quality"
                                    }
                                }
                            ]
                        }
                    },
                    "score_mode": "avg"
                }
            }
        }

        try:
            result = self.es.search(index=index, body=nested_query, size=5)

            print(f"📊 Products with excellent reviews: {result['hits']['total']['value']}")

            for hit in result['hits']['hits']:
                product = hit['_source']
                print(f"   📦 {product['name']} (Score: {hit['_score']:.2f})")

        except Exception as e:
            print(f"❌ Nested query error: {e}")

    def demo_geo_queries(self, index: str = "stores"):
        """
        Geo-spatial query demo
        """
        print("\n🌍 Geo-spatial Query Demo")
        print("=" * 30)

        # Geo distance query
        geo_query = {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "geo_distance": {
                                "distance": "10km",
                                "location": {
                                    "lat": 41.0082,
                                    "lon": 28.9784  # Istanbul coordinates
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [
                {
                    "_geo_distance": {
                        "location": {
                            "lat": 41.0082,
                            "lon": 28.9784
                        },
                        "order": "asc",
                        "unit": "km"
                    }
                }
            ]
        }

        try:
            result = self.es.search(index=index, body=geo_query, size=5)

            print(f"📍 Stores within 10km: {result['hits']['total']['value']}")

            for hit in result['hits']['hits']:
                store = hit['_source']
                distance = hit['sort'][0]
                print(f"   🏪 {store.get('name', 'Unknown Store')} - {distance:.2f}km away")

        except Exception as e:
            print(f"❌ Geo query error: {e}")

def demo_advanced_search():
    """
    Advanced search demo
    """
    print("🔍 Elasticsearch Advanced Search Demo")
    print("=" * 50)

    # Query builder oluştur
    advanced_queries = ElasticsearchAdvancedQueries()

    # Complex product search
    advanced_queries.demo_complex_product_search()

    # Nested queries
    advanced_queries.demo_nested_queries()

    # Geo queries
    advanced_queries.demo_geo_queries()

    print("\n✅ Advanced search demo tamamlandı!")

if __name__ == "__main__":
    demo_advanced_search()
```

## 📊 Advanced Aggregations

### Metric Aggregations

```json
{
  "size": 0,
  "aggs": {
    "price_stats": {
      "stats": {
        "field": "price"
      }
    },
    "avg_rating": {
      "avg": {
        "field": "rating"
      }
    },
    "total_sales": {
      "sum": {
        "field": "sales_amount"
      }
    },
    "price_percentiles": {
      "percentiles": {
        "field": "price",
        "percents": [25, 50, 75, 95, 99]
      }
    }
  }
}
```

### Bucket Aggregations

```json
{
  "size": 0,
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
        "price_ranges": {
          "range": {
            "field": "price",
            "ranges": [
              { "to": 100 },
              { "from": 100, "to": 500 },
              { "from": 500, "to": 1000 },
              { "from": 1000 }
            ]
          }
        }
      }
    },
    "monthly_sales": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "month",
        "format": "yyyy-MM"
      },
      "aggs": {
        "revenue": {
          "sum": {
            "field": "sales_amount"
          }
        }
      }
    }
  }
}
```

### Pipeline Aggregations

```json
{
  "size": 0,
  "aggs": {
    "monthly_sales": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "month"
      },
      "aggs": {
        "revenue": {
          "sum": {
            "field": "sales_amount"
          }
        }
      }
    },
    "revenue_derivative": {
      "derivative": {
        "buckets_path": "monthly_sales>revenue"
      }
    },
    "moving_avg": {
      "moving_avg": {
        "buckets_path": "monthly_sales>revenue",
        "window": 3,
        "model": "simple"
      }
    }
  }
}
```

## 🧪 Hands-on Tasks

### Task 1: E-commerce Search Engine

**Hedef**: Kapsamlı e-ticaret arama sistemi

**Gereksinimler**:

- Multi-field search with boosting
- Faceted search (kategori, fiyat, rating)
- Auto-complete ve spell correction
- Personalized search results

### Task 2: Real-time Analytics Dashboard

**Hedef**: Real-time business analytics

**Gereksinimler**:

- Time-series aggregations
- Multi-level grouping
- Trend analysis
- Alerting on thresholds

### Task 3: Log Analysis System

**Hedef**: Application log analysis

**Gereksinimler**:

- Full-text log search
- Error pattern detection
- Performance metrics
- Geo-location analysis

## ✅ Checklist

Bu bölümü tamamladıktan sonra:

- [ ] Query DSL'in tüm component'lerini kullanabiliyorum
- [ ] Complex bool queries yazabiliyorum
- [ ] Full-text search optimization yapabiliyorum
- [ ] Advanced aggregations kullanabiliyorum
- [ ] Nested ve parent-child queries yazabiliyorum
- [ ] Geo-spatial search implementasyonu yapabiliyorum
- [ ] Search performance optimization uygulayabiliyorum
- [ ] Real-time analytics sistemleri geliştirebiliyorum

## ⚠️ Common Mistakes

### 1. Too Many Should Clauses

**Problem**: Bool query'de çok fazla should clause
**Çözüm**: minimum_should_match kullan, relevance tuning

### 2. Expensive Aggregations

**Problem**: Çok detaylı aggregation'lar performance sorunları
**Çözüm**: Sampling, composite aggregations

### 3. Deep Pagination

**Problem**: Yüksek from offset'ler yavaş
**Çözüm**: Search after, scroll API

## 🔗 İlgili Bölümler

- **Önceki**: [CRUD ve Index Management](02-crud-index-management.md)
- **Sonraki**: [Production Deployment](04-production-deployment.md)
- **İlgili**: [Kibana Dashboards](05-kibana-dashboards.md)

---

**Sonraki Adım**: Production deployment için [Production Best Practices](04-production-deployment.md) bölümüne geçin! 🚀
