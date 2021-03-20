class Environment:

    class PRODUCTION:
        pass

    class TESTING:
        pass


from .production import Production
from .testing import Testing
from .pipeline import Pipeline
