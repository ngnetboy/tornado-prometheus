import logging

def aninfo(*args, **kwargs):
    logging.info(*args, **kwargs)

def anexception(*args, **kwargs):
    logging.exception(*args, **kwargs)

def andebug(*args, **kwargs):
    logging.debug(*args, **kwargs)

def anerror(*args, **kwargs):
    logging.error(*args, **kwargs)
