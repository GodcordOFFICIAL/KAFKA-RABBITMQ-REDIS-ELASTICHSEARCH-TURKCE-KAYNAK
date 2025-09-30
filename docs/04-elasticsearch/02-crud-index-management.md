# Elasticsearch CRUD Operations ve Index Management

## 📋 Özet

Bu bölümde Elasticsearch'te document lifecycle yönetimi, advanced indexing technikleri, mapping optimization ve bulk operations konularını detaylı olarak ele alacağız. Production-ready Elasticsearch uygulamaları için gerekli tüm CRUD operasyonlarını öğreneceksiniz.

## 🎯 Learning Objectives

Bu bölümü tamamladığında:

- ✅ Advanced document CRUD operations yapabileceksin
- ✅ Index templates ve lifecycle policies oluşturabileceksin
- ✅ Mapping optimization ve dynamic mapping kullanabileceksin
- ✅ Bulk operations ve performance tuning yapabileceksin
- ✅ Version control ve conflict resolution uygulayabileceksin
- ✅ Index aliases ve rollover strategies kullanabileceksin

## 📋 Prerequisites

- Elasticsearch temelleri bilgisi
- REST API kullanımı
- JSON formatı anlayışı
- Basic HTTP status codes

## 📄 Advanced Document Operations

### Document Versioning

Elasticsearch her document için otomatik versioning sağlar:

```json
// Document oluştur
PUT /products/_doc/1
{
  "name": "Laptop",
  "price": 1000,
  "category": "electronics"
}

// Response: version 1
{
  "_index": "products",
  "_id": "1",
  "_version": 1,
  "result": "created"
}

// Update with version control
PUT /products/_doc/1?version=1
{
  "name": "Gaming Laptop",
  "price": 1200,
  "category": "electronics"
}
```

### Conditional Updates

```json
// Only update if document exists
POST /products/_update/1
{
  "doc": {
    "price": 950
  },
  "detect_noop": true
}

// Update with script
POST /products/_update/1
{
  "script": {
    "source": "ctx._source.price -= params.discount",
    "params": {
      "discount": 100
    }
  }
}

// Upsert operation
POST /products/_update/2
{
  "doc": {
    "name": "Tablet",
    "price": 500
  },
  "doc_as_upsert": true
}
```

### Multi-Document Operations

```json
// Multi-get
GET /_mget
{
  "docs": [
    {
      "_index": "products",
      "_id": "1"
    },
    {
      "_index": "products",
      "_id": "2",
      "_source": ["name", "price"]
    }
  ]
}

// Update by query
POST /products/_update_by_query
{
  "script": {
    "source": "ctx._source.price *= 1.1"
  },
  "query": {
    "term": {
      "category": "electronics"
    }
  }
}

// Delete by query
POST /products/_delete_by_query
{
  "query": {
    "range": {
      "price": {
        "lt": 100
      }
    }
  }
}
```

## 🏗️ Index Templates ve Lifecycle

### Index Templates

```json
// Index template oluştur
PUT /_index_template/product_template
{
  "index_patterns": ["products-*"],
  "priority": 200,
  "template": {
    "settings": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "refresh_interval": "30s",
      "analysis": {
        "analyzer": {
          "product_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "stop"]
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
        "price": {
          "type": "double"
        },
        "category": {
          "type": "keyword"
        },
        "description": {
          "type": "text",
          "analyzer": "product_analyzer"
        },
        "created_at": {
          "type": "date",
          "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
        },
        "tags": {
          "type": "keyword"
        },
        "specifications": {
          "type": "object",
          "dynamic": true
        },
        "location": {
          "type": "geo_point"
        }
      }
    }
  }
}

// Component template (reusable pieces)
PUT /_component_template/timestamp_template
{
  "template": {
    "mappings": {
      "properties": {
        "created_at": {
          "type": "date"
        },
        "updated_at": {
          "type": "date"
        }
      }
    }
  }
}
```

### Index Lifecycle Management (ILM)

```json
// ILM policy oluştur
PUT /_ilm/policy/product_policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "10gb",
            "max_age": "30d",
            "max_docs": 1000000
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "30d",
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
        "min_age": "90d",
        "actions": {
          "set_priority": {
            "priority": 0
          },
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "delete": {
        "min_age": "365d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}

// Template'e ILM policy ekle
PUT /_index_template/product_template_with_ilm
{
  "index_patterns": ["products-*"],
  "template": {
    "settings": {
      "index.lifecycle.name": "product_policy",
      "index.lifecycle.rollover_alias": "products"
    }
  }
}
```

## 🔧 Advanced Mapping

### Dynamic Mapping Control

```json
PUT /flexible_products
{
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "name": {
        "type": "text"
      },
      "specifications": {
        "type": "object",
        "dynamic": true,
        "properties": {
          "cpu": {
            "type": "text"
          }
        }
      },
      "metadata": {
        "type": "object",
        "dynamic": "false"
      }
    }
  }
}

// Dynamic templates
PUT /smart_products
{
  "mappings": {
    "dynamic_templates": [
      {
        "strings_as_keywords": {
          "match_mapping_type": "string",
          "match": "*_id",
          "mapping": {
            "type": "keyword"
          }
        }
      },
      {
        "dates": {
          "match": "*_date",
          "mapping": {
            "type": "date",
            "format": "yyyy-MM-dd"
          }
        }
      },
      {
        "numbers": {
          "match_mapping_type": "long",
          "match": "quantity_*",
          "mapping": {
            "type": "integer"
          }
        }
      }
    ]
  }
}
```

### Multi-Field Mapping

```json
PUT /analyzed_products
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "raw": {
            "type": "keyword"
          },
          "ngram": {
            "type": "text",
            "analyzer": "ngram_analyzer"
          },
          "completion": {
            "type": "completion"
          }
        }
      }
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "ngram_analyzer": {
          "tokenizer": "ngram_tokenizer"
        }
      },
      "tokenizer": {
        "ngram_tokenizer": {
          "type": "ngram",
          "min_gram": 2,
          "max_gram": 3
        }
      }
    }
  }
}
```

## 💻 Python Advanced CRUD Implementation

```python
from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timedelta
import json
import uuid
from typing import List, Dict, Any, Optional

class ElasticsearchCRUD:
    """
    Advanced Elasticsearch CRUD operations
    """

    def __init__(self, hosts=['localhost:9200'], **kwargs):
        self.es = Elasticsearch(hosts, **kwargs)

    def create_index_with_template(self, index_name: str, template_config: Dict):
        """
        Template ile index oluştur
        """
        try:
            # Index template oluştur
            template_name = f"{index_name}_template"
            self.es.indices.put_index_template(
                name=template_name,
                body=template_config
            )

            # Index oluştur
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name)
                print(f"✅ Index '{index_name}' template ile oluşturuldu")

            return True

        except Exception as e:
            print(f"❌ Index oluşturma hatası: {e}")
            return False

    def document_exists(self, index: str, doc_id: str) -> bool:
        """
        Document'in var olup olmadığını kontrol et
        """
        try:
            return self.es.exists(index=index, id=doc_id)
        except:
            return False

    def create_document(self, index: str, document: Dict, doc_id: str = None) -> Dict:
        """
        Document oluştur (version control ile)
        """
        try:
            if doc_id is None:
                doc_id = str(uuid.uuid4())

            # Timestamp ekle
            document['created_at'] = datetime.now().isoformat()
            document['updated_at'] = document['created_at']

            result = self.es.index(
                index=index,
                id=doc_id,
                body=document,
                op_type='create'  # Sadece yeni document oluştur
            )

            print(f"✅ Document oluşturuldu: {doc_id}")
            return {
                'success': True,
                'id': doc_id,
                'version': result['_version'],
                'result': result['result']
            }

        except Exception as e:
            print(f"❌ Document oluşturma hatası: {e}")
            return {'success': False, 'error': str(e)}

    def get_document(self, index: str, doc_id: str,
                    include_fields: List[str] = None) -> Optional[Dict]:
        """
        Document getir (field filtering ile)
        """
        try:
            params = {'index': index, 'id': doc_id}

            if include_fields:
                params['_source'] = include_fields

            result = self.es.get(**params)

            return {
                'found': True,
                'source': result['_source'],
                'version': result['_version'],
                'id': result['_id']
            }

        except Exception as e:
            print(f"❌ Document getirme hatası: {e}")
            return {'found': False, 'error': str(e)}

    def update_document(self, index: str, doc_id: str,
                       update_data: Dict, version: int = None) -> Dict:
        """
        Document güncelle (version control ile)
        """
        try:
            # Update body hazırla
            update_body = {
                'doc': {
                    **update_data,
                    'updated_at': datetime.now().isoformat()
                },
                'detect_noop': True
            }

            params = {
                'index': index,
                'id': doc_id,
                'body': update_body
            }

            # Version control
            if version:
                params['version'] = version

            result = self.es.update(**params)

            print(f"✅ Document güncellendi: {doc_id}")
            return {
                'success': True,
                'version': result['_version'],
                'result': result['result']
            }

        except Exception as e:
            print(f"❌ Document güncelleme hatası: {e}")
            return {'success': False, 'error': str(e)}

    def upsert_document(self, index: str, doc_id: str, document: Dict) -> Dict:
        """
        Document upsert (oluştur veya güncelle)
        """
        try:
            timestamp = datetime.now().isoformat()

            # Upsert body
            upsert_body = {
                'doc': {
                    **document,
                    'updated_at': timestamp
                },
                'upsert': {
                    **document,
                    'created_at': timestamp,
                    'updated_at': timestamp
                }
            }

            result = self.es.update(
                index=index,
                id=doc_id,
                body=upsert_body
            )

            print(f"✅ Document upsert: {doc_id} ({result['result']})")
            return {
                'success': True,
                'version': result['_version'],
                'result': result['result']
            }

        except Exception as e:
            print(f"❌ Upsert hatası: {e}")
            return {'success': False, 'error': str(e)}

    def delete_document(self, index: str, doc_id: str, version: int = None) -> Dict:
        """
        Document sil (version control ile)
        """
        try:
            params = {'index': index, 'id': doc_id}

            if version:
                params['version'] = version

            result = self.es.delete(**params)

            print(f"✅ Document silindi: {doc_id}")
            return {
                'success': True,
                'result': result['result']
            }

        except Exception as e:
            print(f"❌ Document silme hatası: {e}")
            return {'success': False, 'error': str(e)}

    def bulk_operations(self, operations: List[Dict]) -> Dict:
        """
        Bulk operations (yüksek performans)
        """
        try:
            # Bulk operations listesi hazırla
            bulk_actions = []

            for op in operations:
                action_type = op.get('action', 'index')
                index = op.get('index')
                doc_id = op.get('id')
                document = op.get('document', {})

                # Action header
                action_header = {action_type: {'_index': index}}
                if doc_id:
                    action_header[action_type]['_id'] = doc_id

                bulk_actions.append(action_header)

                # Document body (sadece index ve update için)
                if action_type in ['index', 'update']:
                    if action_type == 'update':
                        bulk_actions.append({'doc': document})
                    else:
                        # Timestamp ekle
                        document['created_at'] = datetime.now().isoformat()
                        bulk_actions.append(document)

            # Bulk request gönder
            result = self.es.bulk(body=bulk_actions)

            # Sonuçları analiz et
            success_count = 0
            error_count = 0
            errors = []

            for item in result['items']:
                operation = list(item.keys())[0]
                op_result = item[operation]

                if 'error' in op_result:
                    error_count += 1
                    errors.append(op_result['error'])
                else:
                    success_count += 1

            print(f"✅ Bulk operations: {success_count} başarılı, {error_count} hata")

            return {
                'success': error_count == 0,
                'total': len(operations),
                'successful': success_count,
                'failed': error_count,
                'errors': errors,
                'took': result['took']
            }

        except Exception as e:
            print(f"❌ Bulk operations hatası: {e}")
            return {'success': False, 'error': str(e)}

    def multi_get(self, requests: List[Dict]) -> Dict:
        """
        Multiple documents getir
        """
        try:
            # Multi-get body hazırla
            mget_body = {'docs': []}

            for req in requests:
                doc_request = {
                    '_index': req['index'],
                    '_id': req['id']
                }

                if 'fields' in req:
                    doc_request['_source'] = req['fields']

                mget_body['docs'].append(doc_request)

            # Multi-get request
            result = self.es.mget(body=mget_body)

            # Sonuçları organize et
            documents = []
            for doc in result['docs']:
                if doc['found']:
                    documents.append({
                        'id': doc['_id'],
                        'source': doc['_source'],
                        'version': doc['_version']
                    })
                else:
                    documents.append({
                        'id': doc['_id'],
                        'found': False
                    })

            print(f"✅ Multi-get: {len(documents)} document")
            return {
                'success': True,
                'documents': documents,
                'took': result.get('took', 0)
            }

        except Exception as e:
            print(f"❌ Multi-get hatası: {e}")
            return {'success': False, 'error': str(e)}

    def update_by_query(self, index: str, query: Dict, script: Dict) -> Dict:
        """
        Query ile bulk update
        """
        try:
            update_body = {
                'query': query,
                'script': script
            }

            result = self.es.update_by_query(
                index=index,
                body=update_body,
                wait_for_completion=True
            )

            print(f"✅ Update by query: {result['updated']} document güncellendi")
            return {
                'success': True,
                'updated': result['updated'],
                'took': result['took']
            }

        except Exception as e:
            print(f"❌ Update by query hatası: {e}")
            return {'success': False, 'error': str(e)}

# Örnek index template
PRODUCT_TEMPLATE = {
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
                        "suggest": {
                            "type": "completion"
                        }
                    }
                },
                "price": {
                    "type": "double"
                },
                "category": {
                    "type": "keyword"
                },
                "description": {
                    "type": "text",
                    "analyzer": "product_search"
                },
                "tags": {
                    "type": "keyword"
                },
                "specifications": {
                    "type": "object",
                    "dynamic": True
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

def demo_advanced_crud():
    """
    Advanced CRUD operations demo
    """
    print("🔧 Advanced Elasticsearch CRUD Demo")
    print("=" * 50)

    # CRUD client oluştur
    crud = ElasticsearchCRUD()

    # Index template ile oluştur
    print("\n1️⃣ Index Template Oluşturma:")
    crud.create_index_with_template("products-demo", PRODUCT_TEMPLATE)

    # Sample products
    products = [
        {
            "name": "MacBook Pro 16",
            "price": 2499.99,
            "category": "laptops",
            "description": "Professional laptop with M1 chip",
            "tags": ["apple", "professional", "m1"],
            "specifications": {
                "cpu": "Apple M1 Pro",
                "ram": "16GB",
                "storage": "512GB SSD"
            }
        },
        {
            "name": "Dell XPS 13",
            "price": 1299.99,
            "category": "laptops",
            "description": "Ultra-portable Windows laptop",
            "tags": ["dell", "ultrabook", "windows"],
            "specifications": {
                "cpu": "Intel i7",
                "ram": "16GB",
                "storage": "256GB SSD"
            }
        }
    ]

    # Bulk create
    print("\n2️⃣ Bulk Document Creation:")
    bulk_ops = []
    for i, product in enumerate(products):
        bulk_ops.append({
            'action': 'index',
            'index': 'products-demo',
            'id': f'product_{i+1}',
            'document': product
        })

    result = crud.bulk_operations(bulk_ops)
    print(f"Bulk result: {result}")

    # Single document operations
    print("\n3️⃣ Single Document Operations:")

    # Get document
    doc_result = crud.get_document('products-demo', 'product_1')
    if doc_result['found']:
        print(f"Found document: {doc_result['source']['name']}")

        # Update document
        update_result = crud.update_document(
            'products-demo',
            'product_1',
            {'price': 2299.99, 'on_sale': True},
            version=doc_result['version']
        )
        print(f"Update result: {update_result}")

    # Upsert new document
    print("\n4️⃣ Upsert Operation:")
    upsert_result = crud.upsert_document(
        'products-demo',
        'product_3',
        {
            "name": "iPad Pro",
            "price": 1099.99,
            "category": "tablets",
            "description": "Professional tablet with M1 chip"
        }
    )
    print(f"Upsert result: {upsert_result}")

    # Multi-get
    print("\n5️⃣ Multi-get Operation:")
    mget_result = crud.multi_get([
        {'index': 'products-demo', 'id': 'product_1', 'fields': ['name', 'price']},
        {'index': 'products-demo', 'id': 'product_2'},
        {'index': 'products-demo', 'id': 'product_3'}
    ])

    for doc in mget_result['documents']:
        if doc.get('found', True):
            print(f"   Document {doc['id']}: {doc['source'].get('name', 'N/A')}")

    # Update by query
    print("\n6️⃣ Update by Query:")
    update_query_result = crud.update_by_query(
        'products-demo',
        {'term': {'category': 'laptops'}},
        {
            'source': 'ctx._source.category = "computers"; ctx._source.updated_by_query = true'
        }
    )
    print(f"Updated by query: {update_query_result}")

if __name__ == "__main__":
    demo_advanced_crud()
```

## 🚀 Performance Optimization

### Bulk Operations Best Practices

1. **Optimal Batch Size**: 1000-5000 documents per batch
2. **Request Size**: Max 100MB per request
3. **Parallel Processing**: Multiple threads for large datasets
4. **Error Handling**: Retry logic for failed operations

### Index Optimization

```python
def optimize_index_settings():
    """
    Index performance optimization
    """
    optimized_settings = {
        "settings": {
            # Write performance
            "refresh_interval": "30s",  # Batch refresh
            "number_of_replicas": 0,    # No replicas during bulk load

            # Search performance
            "index.queries.cache.enabled": True,
            "index.query.default_field": ["name", "description"],

            # Memory optimization
            "index.codec": "best_compression",

            # Routing
            "index.routing_partition_size": 1
        }
    }

    return optimized_settings
```

## ✅ Checklist

Bu bölümü tamamladıktan sonra:

- [ ] Advanced document CRUD operations yapabilirim
- [ ] Index templates kullanabilirim
- [ ] Bulk operations implementasyonu yapabilirim
- [ ] Version control ve conflict resolution uygulayabilirim
- [ ] Dynamic mapping ve templates kullanabilirim
- [ ] Performance optimization yapabilirim
- [ ] Index lifecycle management uygulayabilirim

## 🔗 İlgili Bölümler

- **Önceki**: [Elasticsearch Temelleri](01-temeller.md)
- **Sonraki**: [Search Queries ve Aggregations](03-search-aggregations.md)
- **İlgili**: [Index Management Best Practices](04-production-deployment.md)

---

**Sonraki Adım**: Complex search queries öğrenmek için [Search Queries ve Aggregations](03-search-aggregations.md) bölümüne geçin! 🔍
