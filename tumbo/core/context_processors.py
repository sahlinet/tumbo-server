from tumbo import __VERSION__ as TUMBO_VERSION


def versions(request):
    return {
        'TUMBO_VERSION': TUMBO_VERSION
    }
