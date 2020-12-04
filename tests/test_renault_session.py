"""Test cases for initialisation of the Kamereon client."""
import aiohttp
import pytest
from aioresponses import aioresponses
from tests import get_file_content
from tests.const import TEST_COUNTRY
from tests.const import TEST_GIGYA_URL
from tests.const import TEST_LOCALE
from tests.const import TEST_LOCALE_DETAILS
from tests.const import TEST_LOGIN_TOKEN
from tests.const import TEST_PASSWORD
from tests.const import TEST_PERSON_ID
from tests.const import TEST_USERNAME
from tests.test_credential_store import get_logged_in_credential_store

from renault_api.exceptions import RenaultException
from renault_api.gigya import GIGYA_LOGIN_TOKEN
from renault_api.renault_session import RenaultSession

FIXTURE_PATH = "tests/fixtures/gigya/"


def get_logged_in_session(
    websession: aiohttp.ClientSession,
) -> RenaultSession:
    """Get initialised RenaultSession."""
    return RenaultSession(
        websession=websession,
        country=TEST_COUNTRY,
        locale_details=TEST_LOCALE_DETAILS,
        credential_store=get_logged_in_credential_store(),
    )


@pytest.fixture
def session(websession: aiohttp.ClientSession) -> RenaultSession:
    """Fixture for testing RenaultSession."""
    return RenaultSession(
        websession=websession,
        country=TEST_COUNTRY,
        locale_details=TEST_LOCALE_DETAILS,
    )


@pytest.mark.asyncio
async def tests_init_locale_only(websession: aiohttp.ClientSession) -> None:
    """Test initialisation with locale only."""
    session = RenaultSession(
        websession=websession,
        locale=TEST_LOCALE,
    )
    assert await session._get_country()
    assert await session._get_gigya_api_key()
    assert await session._get_gigya_root_url()
    assert await session._get_kamereon_api_key()
    assert await session._get_kamereon_root_url()


@pytest.mark.asyncio
async def tests_init_country_only(websession: aiohttp.ClientSession) -> None:
    """Test initialisation with country only."""
    session = RenaultSession(
        websession=websession,
        country=TEST_COUNTRY,
    )
    assert await session._get_country()
    with pytest.raises(
        RenaultException,
        match="Credential `gigya-api-key` not found in credential cache.",
    ):
        assert await session._get_gigya_api_key()
    with pytest.raises(
        RenaultException,
        match="Credential `gigya-root-url` not found in credential cache.",
    ):
        assert await session._get_gigya_root_url()
    with pytest.raises(
        RenaultException,
        match="Credential `kamereon-api-key` not found in credential cache.",
    ):
        assert await session._get_kamereon_api_key()
    with pytest.raises(
        RenaultException,
        match="Credential `kamereon-root-url` not found in credential cache.",
    ):
        assert await session._get_kamereon_root_url()


@pytest.mark.asyncio
async def tests_init_locale_details_only(websession: aiohttp.ClientSession) -> None:
    """Test initialisation with locale_details only."""
    session = RenaultSession(
        websession=websession,
        locale_details=TEST_LOCALE_DETAILS,
    )
    with pytest.raises(
        RenaultException,
        match="Credential `country` not found in credential cache.",
    ):
        assert await session._get_country()
    assert await session._get_gigya_api_key()
    assert await session._get_gigya_root_url()
    assert await session._get_kamereon_api_key()
    assert await session._get_kamereon_root_url()


@pytest.mark.asyncio
async def tests_init_locale_and_details(websession: aiohttp.ClientSession) -> None:
    """Test initialisation with locale and locale_details."""
    session = RenaultSession(
        websession=websession,
        locale=TEST_LOCALE,
        locale_details=TEST_LOCALE_DETAILS,
    )
    assert await session._get_country()
    assert await session._get_gigya_api_key()
    assert await session._get_gigya_root_url()
    assert await session._get_kamereon_api_key()
    assert await session._get_kamereon_root_url()


@pytest.mark.asyncio
async def tests_init_locale_country(websession: aiohttp.ClientSession) -> None:
    """Test initialisation with locale and country."""
    session = RenaultSession(
        websession=websession,
        locale=TEST_LOCALE,
        country=TEST_COUNTRY,
    )
    assert await session._get_country()
    assert await session._get_gigya_api_key()
    assert await session._get_gigya_root_url()
    assert await session._get_kamereon_api_key()
    assert await session._get_kamereon_root_url()


@pytest.mark.asyncio
async def test_not_logged_in(session: RenaultSession) -> None:
    """Test errors when not logged in."""
    with pytest.raises(
        RenaultException,
        match=f"Credential `{GIGYA_LOGIN_TOKEN}` not found in credential cache.",
    ):
        await session._get_login_token()
    with pytest.raises(
        RenaultException,
        match=f"Credential `{GIGYA_LOGIN_TOKEN}` not found in credential cache.",
    ):
        await session._get_person_id()
    with pytest.raises(
        RenaultException,
        match=f"Credential `{GIGYA_LOGIN_TOKEN}` not found in credential cache.",
    ):
        await session._get_jwt()


@pytest.mark.asyncio
async def test_login(session: RenaultSession) -> None:
    """Test login/person/jwt response."""
    with aioresponses() as mocked_responses:
        mocked_responses.post(
            f"{TEST_GIGYA_URL}/accounts.login",
            status=200,
            body=get_file_content(f"{FIXTURE_PATH}/login.json"),
            headers={"content-type": "text/javascript"},
        )
        mocked_responses.post(
            f"{TEST_GIGYA_URL}/accounts.getAccountInfo",
            status=200,
            body=get_file_content(f"{FIXTURE_PATH}/get_account_info.json"),
            headers={"content-type": "text/javascript"},
        )
        mocked_responses.post(
            f"{TEST_GIGYA_URL}/accounts.getJWT",
            status=200,
            body=get_file_content(f"{FIXTURE_PATH}/get_jwt.json"),
            headers={"content-type": "text/javascript"},
        )

        await session.login(TEST_USERNAME, TEST_PASSWORD)
        assert await session._get_login_token() == TEST_LOGIN_TOKEN
        assert len(mocked_responses.requests) == 1

        assert await session._get_person_id() == TEST_PERSON_ID
        assert len(mocked_responses.requests) == 2

        assert await session._get_jwt()
        assert len(mocked_responses.requests) == 3

    with aioresponses() as mocked_responses:
        # Ensure further requests use cache
        assert await session._get_person_id() == TEST_PERSON_ID
        assert await session._get_jwt()
        assert len(mocked_responses.requests) == 0