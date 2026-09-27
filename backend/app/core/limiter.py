try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)
except ImportError:
    class DummyLimiter:
        """Fallback no-op limiter when slowapi is unavailable."""
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    limiter = DummyLimiter()

