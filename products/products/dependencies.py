import json
from nameko.extensions import DependencyProvider
import redis


REDIS_URI_KEY = 'REDIS_URI'


class NotFound(Exception):
    pass


class StorageWrapper:
    """
    Product storage

    A very simple Nameko dependency example. This is a simplified
    implementation of products database based on Redis key value store.
    Holding the product ID increments or keeping sorted sets of product
    names for ordering the products is out of the scope of this example.

    """

    NotFound = NotFound

    def __init__(self, client):
        self.client = client

    def _format_key(self, product_id):
        return 'products:{}'.format(product_id)

    def _from_hash(self, document):
        return {
            'id': int(document[b'id']),
            'title': document[b'title'].decode('utf-8'),
            'passenger_capacity': int(document[b'passenger_capacity']),
            'maximum_speed': int(document[b'maximum_speed']),
            'in_stock': int(document[b'in_stock'])
        }

    def get(self, product_id):
        product = self.client.hgetall(self._format_key(product_id))
        if not product:
            raise NotFound('Product ID {} does not exist'.format(product_id))
        else:
            return self._from_hash(product)

    def list(self):
        keys = self.client.keys(self._format_key('*'))
        for key in keys:
            yield self._from_hash(self.client.hgetall(key))

    def create(self, product):
        self.client.hmset(
            self._format_key(product['id']),
            product)

    def decrement_stock(self, product_id, amount):
        return self.client.hincrby(
            self._format_key(product_id), 'in_stock', -amount)


class Storage(DependencyProvider):

    def setup(self):
        self.client = redis.StrictRedis.from_url(
            self.container.config.get(REDIS_URI_KEY))

    def get_dependency(self, worker_ctx):
        return StorageWrapper(self.client)
