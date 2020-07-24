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
