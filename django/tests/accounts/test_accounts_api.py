from datetime import timedelta

# noinspection PyPackageRequirements
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from apps.accounts.models import User, UserToken
from apps.accounts.serializers import UserSerializer
from tests.utils import assert_response, generate_password, get_user_url


def prepare_and_register(api_client: APIClient, user_factory):
    """Prepares and registers a new user."""
    user: User = user_factory(_save=False)
    data = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
    return api_client.post(get_user_url(), data | {
        'password': generate_password(),
    }), data


@pytest.mark.django_db
def test_user_register__password_missing(api_client: APIClient, user_factory):
    """Test user registration (missing password)."""
    response = api_client.post(get_user_url(), {
        'email': user_factory(_save=False).email,
    })
    assert_response(response, 400, {
        'password': ["This field is required."]
    })

@pytest.mark.django_db
def test_user_register__email_missing(api_client):
    """Test user registration (missing email)."""
    response = api_client.post(get_user_url(), {
        'password': generate_password(),
    })
    assert_response(response, 400, {
        'email': ["This field is required."]
    })

@pytest.mark.django_db
def test_user_register__password_empty(api_client: APIClient, user_factory):
    """Test user registration (empty password)."""
    response = api_client.post(get_user_url(), {
        'email': user_factory(_save=False).email,
        'password': '',
    })
    assert_response(response, 400, {
        'password': ["This field may not be blank."]
    })

@pytest.mark.django_db
def test_user_register__password_simple(api_client: APIClient, user_factory):
    """Test user registration (one-digit password)."""
    response = api_client.post(get_user_url(), {
        'email': user_factory(_save=False).email,
        'password': '1',
    })
    assert_response(response, 400, {
        'password': [
            "This password is too short. It must contain at least 8 characters.",
            "This password is too common.",
            "This password is entirely numeric."
        ]
    })

@pytest.mark.django_db
def test_user_register__password_common_numeric(api_client: APIClient, user_factory):
    """Test user registration (common numeric password)."""
    response = api_client.post(get_user_url(), {
        'email': user_factory(_save=False).email,
        'password': '1234567890',
    })
    assert_response(response, 400, {
        'password': [
            "This password is too common.",
            "This password is entirely numeric."
        ]
    })

@pytest.mark.django_db
def test_user_register__password_common_alpha(api_client: APIClient, user_factory):
    """Test user registration (common alpha password)."""
    response = api_client.post(get_user_url(), {
        'email': user_factory(_save=False).email,
        'password': 'qwertyui',
    })
    assert_response(response, 400, {
        'password': ["This password is too common."]
    })

@pytest.mark.django_db
def test_user_register__password_similar_to_email(api_client: APIClient):
    """Test user registration (password resembles email)."""
    response = api_client.post(get_user_url(), {
        'email': 'test@test.com',
        'password': 'Test1@test.com',
    })
    assert_response(response, 400, {
        'password': ["The password is too similar to the email address."]
    })

@pytest.mark.django_db
def test_user_register__bare_minimum(api_client: APIClient, user_factory):
    """Test user registration (just email and password)."""
    data = {
        'email': user_factory(_save=False).email,
    }
    password = generate_password()
    response = api_client.post(get_user_url(), data | {
        'password': password,
    })
    assert_response(response, 201, data | {
        'id': User.objects.order_by('-created_at').last().id,
        'first_name': '',
        'last_name': ''
    })

@pytest.mark.django_db
def test_user_register__success(api_client: APIClient, user_factory, mailoutbox):
    """Test user registration (full data)."""
    # Check user registered.
    response, data = prepare_and_register(api_client, user_factory)
    assert_response(response, 201, data | {
        'id': User.objects.order_by('-created_at').last().id,
    })

    # Check that the verification email was sent.
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Email verification"

@pytest.mark.django_db
def test_user_register__exists(api_client: APIClient, user_factory):
    """Test user registration (existing user)."""
    user = user_factory()
    response = api_client.post(get_user_url(), {
        'email': user.email,
        'password': generate_password(),
    })
    assert_response(response, 400, {
        'email': ["user with this email address already exists."]
    })

@pytest.mark.django_db
def test_user_get__anonymous(api_client: APIClient, user_factory):
    """Test user retrieve (anonymous request)."""
    user = user_factory()
    response = api_client.get(get_user_url(user.pk))
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_user_get__wrong_token(api_client: APIClient, user_factory):
    """Test user retrieve (incorrect access token)."""
    user = user_factory()
    api_client.credentials(HTTP_AUTHORIZATION='Bearer TralaleroTralala')
    response = api_client.get(get_user_url(user.pk))
    assert_response(response, 401, {
        'detail': "Given token not valid for any token type",
        'code': 'token_not_valid',
        'messages': [{
            'token_class': 'AccessToken',
            'token_type': 'access',
            'message': 'Token is invalid'
        }]
    })

@pytest.mark.django_db
def test_user_get__another_user(api_client_auth: APIClient, user_factory):
    """Test user retrieve (as another user)."""
    user = user_factory()
    response = api_client_auth.get(get_user_url(user.pk))
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action."
    })

@pytest.mark.django_db
def test_user_get__success(api_client_auth: APIClient):
    """Test user retrieve."""
    # noinspection PyUnresolvedReferences
    user = api_client_auth._user
    response = api_client_auth.get(get_user_url(user.pk))
    assert_response(response, 200, UserSerializer(instance=user).data)

@pytest.mark.django_db
def test_user_patch__anonymous(api_client: APIClient, user_factory):
    """Test user update (anonymous request)."""
    user = user_factory()
    data = UserSerializer(instance=user).data
    response = api_client.patch(get_user_url(user.pk), data)
    assert_response(response, 401, {
        'detail': "Authentication credentials were not provided."
    })

@pytest.mark.django_db
def test_user_patch__another_user(api_client_auth: APIClient, user_factory):
    """Test user update (as another user)."""
    user = user_factory()
    data = UserSerializer(instance=user).data
    response = api_client_auth.patch(get_user_url(user.pk), data)
    assert_response(response, 403, {
        'detail': "You do not have permission to perform this action."
    })

@pytest.mark.django_db
def test_user_patch__success(api_client_auth: APIClient):
    """Test user update."""
    # noinspection PyUnresolvedReferences
    user = api_client_auth._user
    data = {
        'first_name': 'Quentin',
        'last_name': 'Tarantino',
    }
    response = api_client_auth.patch(get_user_url(user.pk), data)
    assert_response(response, 200, UserSerializer(instance=user).data | data)

@pytest.mark.django_db
def test_email_verify__wrong_user(api_client: APIClient, user_factory):
    """Test user email verification (wrong user)."""
    response, data = prepare_and_register(api_client, user_factory)
    uid = response.data.get('id')
    token = UserToken.objects.get(user_id=uid)

    response = api_client.post(get_user_url(uid + 1, 'verify'), {
        'token': token.value # The token is valid!
    })
    assert_response(response, 404, {
        'detail': "User does not exist."
    })

@pytest.mark.django_db
def test_email_verify__wrong_token(api_client: APIClient, user_factory):
    """Test user email verification (wrong token)."""
    response, data = prepare_and_register(api_client, user_factory)
    uid = response.data.get('id')

    response = api_client.post(get_user_url(uid, 'verify'), {
        'token': "Something that is definitely not a valid token"
    })
    assert_response(response, 404, {
        'detail': "Token does not exist."
    })

@pytest.mark.django_db
def test_email_verify__token_expired(api_client: APIClient, user_factory):
    """Test user email verification (token expired)."""
    response, data = prepare_and_register(api_client, user_factory)
    uid = response.data.get('id')

    # Age the token!
    token = UserToken.objects.get(user_id=uid)
    token.expires_at -= (settings.USER_TOKEN_LIFETIME + timedelta(days=1))
    token.save()

    response = api_client.post(get_user_url(uid, 'verify'), {
        'token': token.value
    })
    assert_response(response, 404, {
        'detail': "Token has expired."
    })

@pytest.mark.django_db
def test_email_verify__successd(api_client: APIClient, user_factory):
    """Test user email verification (email verified)."""
    response, data = prepare_and_register(api_client, user_factory)
    uid = response.data.get('id')
    token = UserToken.objects.get(user_id=uid)

    response = api_client.post(get_user_url(uid, 'verify'), {
        'token': token.value
    })
    assert_response(response, 200, {
        'detail': "Email verified."
    })

@pytest.mark.django_db
def test_email_verify__new_email(api_client: APIClient, user_factory,
        mailoutbox):
    """Test user email verification (send another email)."""
    response, data = prepare_and_register(api_client, user_factory)
    uid = response.data.get('id')

    # Save the original token for future comparison.
    token1 = UserToken.objects.get(user_id=uid)

    response = api_client.post(get_user_url(uid, 'verify'))
    assert_response(response, 200, {
        'detail': "Email sent."
    })

    # There is still only one token...
    assert UserToken.objects.filter(user_id=uid).count() == 1

    # ...but it has a different value.
    token2 = UserToken.objects.get(user_id=uid)
    assert token1.value != token2.value

    # The original token is no more valid.
    response = api_client.post(get_user_url(uid, 'verify'), {
        'token': token1.value
    })
    assert_response(response, 404, {
        'detail': "Token does not exist."
    })

    # But the new one is valid.
    response = api_client.post(get_user_url(uid, 'verify'), {
        'token': token2.value
    })
    assert_response(response, 200, {
        'detail': "Email verified."
    })

    # Two verification emails were sent at this moment.
    assert len(mailoutbox) == 2
    assert mailoutbox[1].subject == "Email verification"

@pytest.mark.django_db
def test_password_restore__get_token(api_client: APIClient, user_factory,
        mailoutbox):
    """Test password restoration (retrieving a token)."""
    user = user_factory(is_verified=True)

    response = api_client.post(get_user_url(user.pk, 'restore'))
    assert_response(response, 200, {
        'detail': "Email sent."
    })

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Restore password"

@pytest.mark.django_db
def test_password_restore__wrong_user(api_client: APIClient, user_factory):
    """Test password restoration (wrong user)."""
    user = user_factory(is_verified=True)

    # This request generates a new token.
    api_client.post(get_user_url(user.pk, 'restore'))
    token = UserToken.objects.get(user_id=user.pk)

    response = api_client.post(get_user_url(user.pk + 1, 'restore'), {
        'token': token.value # The token is valid!
    })
    assert_response(response, 404, {
        'detail': "User does not exist."
    })

@pytest.mark.django_db
def test_password_restore__wrong_token(api_client: APIClient, user_factory):
    """Test password restoration (wrong token)."""
    user = user_factory(is_verified=True)

    # This request generates a new token.
    api_client.post(get_user_url(user.pk, 'restore'))

    response = api_client.post(get_user_url(user.pk, 'restore'), {
        'token': "Something that is definitely not a valid token"
    })
    assert_response(response, 404, {
        'detail': "Token does not exist."
    })

@pytest.mark.django_db
def test_password_restore__token_expired(api_client: APIClient, user_factory):
    """Test password restoration (token expired)."""
    user = user_factory(is_verified=True)

    # This request generates a new token.
    api_client.post(get_user_url(user.pk, 'restore'))
    token = UserToken.objects.get(user_id=user.pk)

    # Age the token!
    token.expires_at -= (settings.USER_TOKEN_LIFETIME + timedelta(days=1))
    token.save()

    response = api_client.post(get_user_url(user.pk, 'restore'), {
        'token': token.value
    })
    assert_response(response, 404, {
        'detail': "Token has expired."
    })

@pytest.mark.django_db
def test_password_restore__no_password(api_client: APIClient, user_factory):
    """Test password restoration (no password)."""
    user = user_factory(is_verified=True)

    # This request generates a new token.
    api_client.post(get_user_url(user.pk, 'restore'))
    token = UserToken.objects.get(user_id=user.pk)

    response = api_client.post(get_user_url(user.pk, 'restore'), {
        'token': token.value
    })
    assert_response(response, 400, {
        'password': ["This field is required."]
    })

@pytest.mark.django_db
def test_password_restore__bad_password(api_client: APIClient, user_factory):
    """Test password restoration (bad password)."""
    user = user_factory(is_verified=True)

    # This request generates a new token.
    api_client.post(get_user_url(user.pk, 'restore'))
    token = UserToken.objects.get(user_id=user.pk)

    response = api_client.post(get_user_url(user.pk, 'restore'), {
        'token': token.value,
        'password': '1'
    })
    assert_response(response, 400, {
        'password': [
            "This password is too short. It must contain at least 8 characters.",
            "This password is too common.",
            "This password is entirely numeric."
        ]
    })

@pytest.mark.django_db
def test_password_restore__success(api_client: APIClient, user_factory):
    """Test password restoration (success)."""
    user = user_factory(is_verified=True)

    # This request generates a new token.
    api_client.post(get_user_url(user.pk, 'restore'))
    token = UserToken.objects.get(user_id=user.pk)

    response = api_client.post(get_user_url(user.pk, 'restore'), {
        'token': token.value,
        'password': generate_password(),
    })
    assert_response(response, 200, {
        'detail': "Password reset."
    })

@pytest.mark.django_db
def test_password_restore__send_email(api_client: APIClient, user_factory,
        mailoutbox):
    """Test password restoration (send another email)."""
    user = user_factory(is_verified=True)

    # This request generates a new token.
    api_client.post(get_user_url(user.pk, 'restore'))
    token1 = UserToken.objects.get(user_id=user.pk)

    # This request generates another token.
    response = api_client.post(get_user_url(user.pk, 'restore'))
    assert_response(response, 200, {
        'detail': "Email sent."
    })

    # There is still only one token...
    assert UserToken.objects.filter(user_id=user.pk).count() == 1

    # ...but it has a different value.
    token2 = UserToken.objects.get(user_id=user.pk)
    assert token1.value != token2.value

    # The original token is no more valid.
    response = api_client.post(get_user_url(user.pk, 'restore'), {
        'token': token1.value
    })
    assert_response(response, 404, {
        'detail': "Token does not exist."
    })

    # But the new one is valid.
    response = api_client.post(get_user_url(user.pk, 'restore'), {
        'token': token2.value,
        'password': generate_password(),
    })
    assert_response(response, 200, {
        'detail': "Password reset."
    })

    # Two verification emails were sent at this moment.
    assert len(mailoutbox) == 2
    assert mailoutbox[1].subject == "Restore password"
