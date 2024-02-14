import requests

from random_words import RandomWords

from . import config

r = RandomWords()


def get_tenant_auth_headers(token):
    """Get the auth headers for the tenant."""

    return {"Authorization": f"Bearer {token}"}


async def get_innkeeper_auth_headers():
    """Get the auth headers for the innkeeper."""

    return {"Authorization": f"Bearer {await get_inkeeper_token()}"}


async def get_inkeeper_token():
    """Get the token for the innkeeper."""

    data = {"wallet_key": config.INNKEEPER_WALLET_KEY}

    res = requests.post(
        f"{config.PROXY_URL}/multitenancy/tenant/{config.INNKEEPER_TENANT_ID}/token",
        json=data,
    )

    return res.json().get("token")


async def create_tenant(tenant_name: str):
    """Create a tenant."""

    # Tenant creates a reservation request, it will auto approve
    res = requests.post(
        f"{config.PROXY_URL}/multitenancy/reservations",
        json={"tenant_name": tenant_name, "contact_email": "asdf@asdf.com"},
    )
    reservation_id = res.json().get("reservation_id")
    reservation_pwd = res.json().get("reservation_pwd")

    # Tenant can now create their wallet
    res = requests.post(
        f"{config.PROXY_URL}/multitenancy/reservations/{reservation_id}/check-in",
        json={"reservation_pwd": reservation_pwd},
    )
    json_res = res.json()
    token = json_res.get("token")

    # Tenant can now register a webhook
    res = requests.put(
        f"{config.PROXY_URL}/tenant/wallet",
        json={
            "wallet_webhook_urls": [
                f"http://host.docker.internal:8000/webhook#{r.random_word().lower()}"
            ]
        },
        headers=get_tenant_auth_headers(token),
    )

    return {
        "tenant_name": tenant_name,
        "token": token,
        "wallet_id": json_res.get("wallet_id"),
        "wallet_key": json_res.get("wallet_key"),
        "wallet_webhook_urls": json_res.get("wallet_webhook_urls"),
    }


async def create_invitation(headers):
    """Create an out-of-band invitation for the tenant."""

    res = requests.post(
        f"{config.PROXY_URL}/out-of-band/create-invitation",
        headers=headers,
        params={"auto_accept": "true"},
        json={
            "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
        },
    )

    return res.json()


async def create_connection(headers, invitation):
    """Create a connection with the invitation."""

    res = requests.post(
        f"{config.PROXY_URL}/out-of-band/receive-invitation",
        headers=headers,
        json=invitation,
    )

    return res.json()

async def send_drpc_request(headers, connection_id, rpc_request):
    """Send a request to the agent for the tenant."""

    res = requests.post(
        f"{config.PROXY_URL}/drpc/request",
        headers=headers,
        json={
            "connection_id": connection_id,
            "request": rpc_request,
        },
    )

    return res.json()

async def send_drpc_response(headers, connection_id, rpc_request_id, rpc_response):
    """Send a response to the agent for the tenant."""

    res = requests.post(
        f"{config.PROXY_URL}/drpc/response",
        headers=headers,
        json={
            "connection_id": connection_id,
            "thread_id": rpc_request_id,
            "response": rpc_response,
        },
    )

    return res.json()