import logging
logger = logging.getLogger(__name__)


class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, keep=True, *args, **kwargs):
        logger.debug("Handle singleton instance for %s with args (keep=%s): %s, %s" % (cls, keep, args, kwargs))
        if keep:
            if cls.instance is None:
                logger.debug("Return and keep singleton instance for %s with args (keep=%s): %s, %s" % (cls, keep, args, kwargs))
                cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
                return cls.instance
            else:
                logger.debug("Return cached singleton instance for %s with args (keep=%s): %s, %s" % (cls, keep, args, kwargs))
                return cls.instance
        else:
            logger.debug("Return new singleton instance for %s with args (keep=%s): %s, %s" % (cls, keep, args, kwargs))
            return super(Singleton, cls).__call__(*args, **kwargs)

        return None
