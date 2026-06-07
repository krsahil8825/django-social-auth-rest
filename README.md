# django-social-auth-rest

Social login for Django REST Framework - with account linking, JWT tokens, and room to grow.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Django 5.0+](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What This Does

`django-social-auth-rest` lets your users sign in with their social accounts (Google, GitHub) and returns JWT tokens your frontend can use right away. It also handles connecting and disconnecting those social accounts after the fact.

**Currently supported providers:** Google, GitHub  
**More providers are coming soon.**

## Features

- Sign in with Google or GitHub - get back JWT access and refresh tokens
- Link or unlink social accounts from an existing user profile
- See which providers a user has connected
- CSRF protection via signed OAuth state tokens (GitHub flow)
- Rate limiting on all auth endpoints
- Optional support for soft-deleted user accounts
- Signals you can hook into for things like welcome emails or analytics

## Requirements

- Python 3.12+
- Django 5.0+
- Django REST Framework 3.15+

The following packages are installed automatically:

- `djangorestframework-simplejwt`
- `google-auth`
- `requests`

## Installation

```bash
pip install django-social-auth-rest
```

## Setup

### 1. Add to `INSTALLED_APPS`

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "django_social_auth_rest",
]
```

### 2. Set up JWT authentication

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}
```

### 3. Configure JWT tokens

```python
# settings.py
from datetime import timedelta

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
```

### 4. Add provider credentials

Add credentials only for the providers you want to use. Providers without credentials are automatically disabled - their endpoints will not be available.

```python
# settings.py

# GitHub (requires both values)
GITHUB_CLIENT_ID = "your-github-client-id"
GITHUB_CLIENT_SECRET = "your-github-client-secret"

# Google (requires only the client ID)
GOOGLE_CLIENT_ID = "your-google-client-id"

# add more providers here as needed
```

See the [Provider Guides](#provider-guides) section for where to get these credentials.

### 5. Register the URLs

Include the base URL module plus each provider you want to enable:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("api/social-auth/", include("django_social_auth_rest.urls")),
    path("api/social-auth/", include("django_social_auth_rest.urls.github")),
    path("api/social-auth/", include("django_social_auth_rest.urls.google")),
    # add more providers here as needed
]
```

You only need to include a provider's URL module if you're using that provider. See the [Provider Guides](#provider-guides) section for details on each provider's endpoints.

### 6. Run migrations

```bash
python manage.py migrate
```

## Optional Settings

These settings have sensible defaults and do not need to be changed unless you have specific requirements.

| Setting                          | Default                    | What It Does                                                                |
| -------------------------------- | -------------------------- | --------------------------------------------------------------------------- |
| `SOCIAL_AUTH_THROTTLE_RATE`      | `"10/minute"`              | Limits how many auth requests a user can make per minute                    |
| `SOCIAL_AUTH_STATE_SALT`         | `"social-auth-state-salt"` | Salt value used to sign OAuth state tokens - change this in production      |
| `SOCIAL_AUTH_STATE_MAX_AGE`      | `300`                      | How long (in seconds) a state token stays valid before expiring             |
| `SOCIAL_AUTH_USER_DELETED_FIELD` | `None`                     | Name of a boolean field on your user model that marks soft-deleted accounts |

## Provider Guides

### GitHub

#### Getting your credentials

1. Go to your GitHub account → **Settings → Developer Settings → OAuth Apps**
2. Click **New OAuth App**
3. Fill in the application details and set your **Authorization callback URL**
4. Copy the **Client ID** and generate a **Client Secret**

#### Settings

```python
# settings.py
GITHUB_CLIENT_ID = "your-github-client-id"
GITHUB_CLIENT_SECRET = "your-github-client-secret"
```

#### Urls

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("api/social-auth/", include("django_social_auth_rest.urls.github")),
]
```

#### How it works

GitHub uses the standard OAuth 2.0 authorization code flow. Your frontend redirects the user to GitHub, which then redirects back with a temporary code. That code is sent to your backend to complete the login.

A signed state token is used to prevent CSRF attacks - your frontend must request one before starting the flow and include it throughout.

```
1. Frontend requests a state token  →  GET /api/social-auth/github/state/
2. Frontend redirects user to GitHub with client_id and state token
3. User authorizes on GitHub, gets redirected back with a code and state
4. Frontend sends code + state to  POST /api/social-auth/github/login/
5. Backend validates the state, exchanges the code, and returns JWT tokens
```

#### Endpoints

**Get a state token** _(required before starting the OAuth flow)_

```http
GET /api/social-auth/github/state/
```

Response:

```json
{
  "state": "<SIGNED_STATE_TOKEN>"
}
```

**Login**

```http
POST /api/social-auth/github/login/
Content-Type: application/json

{
  "code": "<AUTHORIZATION_CODE>",
  "state": "<SIGNED_STATE_TOKEN>"
}
```

Response:

```json
{
  "access": "<JWT_ACCESS_TOKEN>",
  "refresh": "<JWT_REFRESH_TOKEN>"
}
```

**Link account** _(requires authentication)_

```http
POST /api/social-auth/github/link/
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json

{
  "code": "<AUTHORIZATION_CODE>",
  "state": "<SIGNED_STATE_TOKEN>"
}
```

Returns `204 No Content` on success.

**Unlink account** _(requires authentication)_

```http
POST /api/social-auth/github/unlink/
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

Returns `204 No Content` on success.

### Google

#### Getting your credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select an existing one)
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Copy the **Client ID**

#### Settings

```python
# settings.py
GOOGLE_CLIENT_ID = "your-google-client-id"
```

#### Urls

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("api/social-auth/", include("django_social_auth_rest.urls.google")),
]
```

#### How it works

Google uses an ID token flow. Your frontend handles the Google sign-in and receives an ID token from Google. It sends that token to your backend, which validates it and issues JWT tokens.

```
1. User signs in with Google on your frontend
2. Frontend receives a Google ID token
3. Frontend sends the token to POST /api/social-auth/google/login/
4. Backend validates the token with Google
5. Backend returns JWT access and refresh tokens
```

#### Endpoints

**Login**

```http
POST /api/social-auth/google/login/
Content-Type: application/json

{
  "token": "<GOOGLE_ID_TOKEN>"
}
```

Response:

```json
{
  "access": "<JWT_ACCESS_TOKEN>",
  "refresh": "<JWT_REFRESH_TOKEN>"
}
```

**Link account** _(requires authentication)_

```http
POST /api/social-auth/google/link/
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json

{
  "token": "<GOOGLE_ID_TOKEN>"
}
```

Returns `204 No Content` on success.

**Unlink account** _(requires authentication)_

```http
POST /api/social-auth/google/unlink/
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

Returns `204 No Content` on success.

## Linked Accounts

Returns a list of all enabled providers and whether the current user has connected each one.

Requires authentication.

```http
GET /api/social-auth/linked-accounts/
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

Response:

```json
{
  "providers": [
    {
      "label": "Google",
      "is_linked": true
    },
    {
      "label": "GitHub",
      "is_linked": false
    }
    // more providers as configured
  ]
}
```

## Soft-Deleted Accounts

If your app uses soft deletion (marking users as deleted rather than removing them from the database), you can block deleted accounts from signing in.

Set `SOCIAL_AUTH_USER_DELETED_FIELD` to the name of the boolean field on your user model:

```python
# settings.py
SOCIAL_AUTH_USER_DELETED_FIELD = "is_deleted"
```

Example user model:

```python
class User(AbstractUser):
    is_deleted = models.BooleanField(default=False)
```

When this is configured, any user with `is_deleted = True` will be blocked from logging in, linking, or creating a new account through social auth.

## Signals

The package sends Django signals for key events. You can connect to these to run your own code - for example, sending a welcome email when a new user registers.

| Signal                      | When it fires                                               |
| --------------------------- | ----------------------------------------------------------- |
| `new_user_registered`       | A new account is created for the first time via social auth |
| `login_successful`          | A user successfully signs in                                |
| `link_account_successful`   | A social account is linked to a user                        |
| `unlink_account_successful` | A social account is removed from a user                     |

All signals include these keyword arguments: `request`, `user`, `provider`.

**Example:**

```python
from django.dispatch import receiver
from django_social_auth_rest.signals import new_user_registered

@receiver(new_user_registered)
def on_new_user(sender, request, user, provider, **kwargs):
    print(f"New user {user.email} joined via {provider}")
    # send welcome email, create profile, etc.
```

## Contributing

Contributions are welcome. If you find a bug or want to suggest an improvement, please open an issue first so we can discuss it.

More authentication providers are planned - if you'd like to add one, open an issue to coordinate.

## License

MIT - see [LICENSE](LICENSE) for details.
