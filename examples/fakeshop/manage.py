#!/usr/bin/env python
"""Django command-line entry point for the fakeshop example project."""

import os
import sys


def main() -> None:
    """Run Django's command-line utility for the fakeshop project."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
