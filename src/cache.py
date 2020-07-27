from collections import OrderedDict

class NullCache:

    def __init__(self, logger):
        self.logger = logger

    def has_media_id(self, media_id):
        self.logger.info(f"Cache: has_media_id({media_id})")
        return False

    def get_media(self, media_id):
        self.logger.info(f"Cache: get_media with {media_id}")

    def set_media(self, media_id, media):
        self.logger.info(f"Cache: set_media with {media_id}")


class LRUCache:

    def __init__(self, logger, capacity=20):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.logger = logger

    def has_media_id(self, media_id):
        return media_id in self.cache

    def get_media(self, media_id):
        if media_id not in self.cache:
            return -1
        else:
            self.logger.info(f"Cache: Return {media_id} from cache")
            self.cache.move_to_end(media_id)
            return self.cache[media_id]

    def set_media(self, media_id, media):
        self.cache[media_id] = media
        self.cache.move_to_end(media_id)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last = False)
