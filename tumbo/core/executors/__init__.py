from django.db import connections

def patch_thread(connections_override):
    """Used in tests.py's for reusing database in threads.
    
    Arguments:
        connections_override {dict} -- connection configuration
    """

    if connections_override:
        # Override this thread's database connections with the ones
        # provided by the main thread.
        for alias, conn in connections_override.items():
            connections[alias] = conn
            #import pprint;pprint.pprint(conn.__dict__)
            #print conn.connection.__dict__