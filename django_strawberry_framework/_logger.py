"""The package logger, in a leaf module so the package ``__init__`` imports it like any name.

The logger name is spelled here and nowhere else. The package
``__init__`` re-exports ``logger`` and subpackages read it through that re-export
(``from .. import logger``; see ``optimizer/__init__.py``). Consumer-facing: the name is
the key clients use in Django's ``LOGGING`` config dict, so it is part of the public
surface even though it is not in ``__all__``.
"""

import logging

logger: logging.Logger = logging.getLogger("django_strawberry_framework")
