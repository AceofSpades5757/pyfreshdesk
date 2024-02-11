[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![PyPI](https://img.shields.io/pypi/v/pyfreshdesk?color=darkred)](https://pypi.org/project/pyfreshdesk/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyfreshdesk?label=Python%20Version&logo=python&logoColor=yellow)](https://pypi.org/project/pyfreshdesk/)
[![PyPI - License](https://img.shields.io/pypi/l/pyfreshdesk?color=green)](https://github.com/AceofSpades5757/pyfreshdesk/blob/main/LICENSE)

[![Tests](https://github.com/AceofSpades5757/pyfreshdesk/actions/workflows/test.yml/badge.svg)](https://github.com/AceofSpades5757/pyfreshdesk/actions/workflows/test.yml)

[![Read the Docs](https://img.shields.io/readthedocs/pyfreshdesk)](https://pyfreshdesk.readthedocs.io/en/latest/)

# Description

Python client library for interacting with Freshdesk.

# Installation

`pip install pyfreshdesk`

# Usage

## Basic

```python
from freshdesk import Client


fd = Client(domain='mydomain', api_key='MY_API_KEY')
```

## Different Plan

```python
from freshdesk import Client
from freshdesk import Plan


fd = Client(
    domain='mydomain',
    api_key='MY_API_KEY',
    plan=Plan.ESTATE,
)
```
