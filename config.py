class Config(object):
    DEBUG = False
    TESTING = True


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    pass
