# django-social-auth-rest

Social login for Django REST Framework - with account linking, JWT tokens, and room to grow.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Django 5.0+](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Read the full docs →](https://krsahil8825.github.io/django-social-auth-rest/)**

## What This Does

`django-social-auth-rest` lets your users sign in with their social accounts (Google, GitHub, etc.) and returns JWT tokens your frontend can use right away. It also handles connecting and disconnecting those social accounts after the fact.

**Currently supported providers:** Google, GitHub
**More providers are coming soon.**

## Features

- Sign in with socail accounts (like google, github) - get back JWT access and refresh tokens
- Link or unlink social accounts from an existing user profile
- See which providers a user has connected
- CSRF protection via signed OAuth state tokens
- Rate limiting on all auth endpoints
- Optional support for soft-deleted user accounts
- Signals you can hook into for things like welcome emails or analytics

## Requirements

- Python 3.12+
- Django 5.0+
- Django REST Framework 3.15+

## Install

```bash
pip install django-social-auth-rest
```

For setup, provider credentials, the API reference, and signals, see the **[documentation site](https://krsahil8825.github.io/django-social-auth-rest/)**:

- [Getting Started](https://krsahil8825.github.io/django-social-auth-rest/guides/getting-started/)
- [GitHub provider guide](https://krsahil8825.github.io/django-social-auth-rest/guides/providers/github/)
- [Google provider guide](https://krsahil8825.github.io/django-social-auth-rest/guides/providers/google/)
- [Linked accounts](https://krsahil8825.github.io/django-social-auth-rest/guides/linked-accounts/)
- [Signals reference](https://krsahil8825.github.io/django-social-auth-rest/reference/signals/)

## Contributing

Contributions are welcome. If you find a bug or want to suggest an improvement, please open an issue first so we can discuss it.

More authentication providers are planned - if you'd like to add one, open an issue to coordinate.

## License

MIT - see [LICENSE](LICENSE) for details.