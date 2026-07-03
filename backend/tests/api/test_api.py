import pytest

from app.agent.tools.image_ocr import ImageOcrTool
from tests.conftest import auth_headers, category_id


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_auth_register_duplicate_login_me(client):
    payload = {"email": "a@example.com", "username": "alice", "display_name": "Alice", "password": "strong-password"}
    assert (await client.post("/api/auth/register", json=payload)).status_code == 201
    assert (await client.post("/api/auth/register", json=payload)).status_code == 409
    duplicate_username = {**payload, "email": "other@example.com"}
    assert (await client.post("/api/auth/register", json=duplicate_username)).status_code == 409
    login = await client.post("/api/auth/login", json=payload)
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@example.com"
    assert me.json()["username"] == "alice"
    assert me.json()["display_name"] == "Alice"


@pytest.mark.asyncio
async def test_auth_update_profile_and_password(client):
    payload = {"email": "profile@example.com", "username": "profile", "display_name": "Profile", "password": "strong-password"}
    assert (await client.post("/api/auth/register", json=payload)).status_code == 201
    login = await client.post("/api/auth/login", json=payload)
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    updated = await client.patch(
        "/api/auth/me",
        json={
            "email": "new-profile@example.com",
            "username": "new_profile",
            "display_name": "New Profile",
            "current_password": "strong-password",
        },
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["email"] == "new-profile@example.com"
    assert updated.json()["username"] == "new_profile"
    assert updated.json()["display_name"] == "New Profile"

    password_update = await client.patch(
        "/api/auth/me",
        json={"current_password": "strong-password", "new_password": "new-strong-password"},
        headers=headers,
    )
    assert password_update.status_code == 200
    assert (await client.post("/api/auth/login", json={"email": "new-profile@example.com", "password": "strong-password"})).status_code == 401
    assert (await client.post("/api/auth/login", json={"email": "new-profile@example.com", "password": "new-strong-password"})).status_code == 200


@pytest.mark.asyncio
async def test_auth_update_profile_conflicts(client):
    first = {"email": "first@example.com", "username": "first", "display_name": "First", "password": "strong-password"}
    second = {"email": "second@example.com", "username": "second", "display_name": "Second", "password": "strong-password"}
    assert (await client.post("/api/auth/register", json=first)).status_code == 201
    assert (await client.post("/api/auth/register", json=second)).status_code == 201
    login = await client.post("/api/auth/login", json=first)
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert (await client.patch("/api/auth/me", json={"display_name": "No Password"}, headers=headers)).status_code == 400
    assert (await client.patch("/api/auth/me", json={"email": "second@example.com", "current_password": "strong-password"}, headers=headers)).status_code == 409
    assert (await client.patch("/api/auth/me", json={"username": "second", "current_password": "strong-password"}, headers=headers)).status_code == 409
    assert (await client.patch("/api/auth/me", json={"current_password": "wrong-password", "new_password": "new-strong-password"}, headers=headers)).status_code == 400


@pytest.mark.asyncio
async def test_transactions_crud_and_user_scope(client, db_session):
    headers = await auth_headers(client, "one@example.com")
    other_headers = await auth_headers(client, "two@example.com")
    products = await category_id(db_session, "products")
    payload = {
        "amount": "1200.00",
        "operation_type": "expense",
        "category_id": products,
        "occurred_at": "2026-07-01",
        "comment": "Покупка продуктов",
    }
    created = await client.post("/api/transactions", json=payload, headers=headers)
    assert created.status_code == 201
    tx_id = created.json()["id"]
    own_list = await client.get("/api/transactions", headers=headers)
    assert own_list.json()["total"] == 1
    other_list = await client.get("/api/transactions", headers=other_headers)
    assert other_list.json()["total"] == 0
    assert (await client.delete(f"/api/transactions/{tx_id}", headers=other_headers)).status_code == 404
    assert (await client.delete(f"/api/transactions/{tx_id}", headers=headers)).status_code == 204
    assert (await client.get("/api/transactions", headers=headers)).json()["total"] == 0


@pytest.mark.asyncio
async def test_stats(client, db_session):
    headers = await auth_headers(client)
    products = await category_id(db_session, "products")
    salary = await category_id(db_session, "salary")
    await client.post("/api/transactions", json={"amount": "1000.00", "operation_type": "income", "category_id": salary, "occurred_at": "2026-07-01", "comment": "Зарплата"}, headers=headers)
    await client.post("/api/transactions", json={"amount": "250.00", "operation_type": "expense", "category_id": products, "occurred_at": "2026-07-01", "comment": "Еда"}, headers=headers)
    summary = (await client.get("/api/stats/summary", headers=headers)).json()
    assert summary == {"income_total": "1000.00", "expense_total": "250.00", "balance": "750.00"}
    by_category = (await client.get("/api/stats/expenses-by-category", headers=headers)).json()
    assert by_category[0]["amount"] == "250.00"


@pytest.mark.asyncio
async def test_text_import_preview_confirm_and_duplicates(client):
    headers = await auth_headers(client)
    text = "01.07.2026 Списание 349,90 RUB Перекрёсток\n01.07.2026 Зачисление 5000,00 RUB Перевод от Иван"
    preview = await client.post("/api/imports/text", json={"text": text}, headers=headers)
    assert preview.status_code == 201
    data = preview.json()
    assert data["job"]["status"] == "needs_review"
    assert len(data["candidates"]) == 2
    first = data["candidates"][0]
    patched = await client.patch(
        f"/api/imports/candidates/{first['id']}",
        json={
            "amount": first["amount"],
            "operation_type": first["operation_type"],
            "category_id": first["category"]["id"],
            "occurred_at": first["occurred_at"],
            "comment": "Исправленный комментарий",
        },
        headers=headers,
    )
    assert patched.status_code == 200
    confirmed = await client.post(
        f"/api/imports/{data['job']['id']}/confirm",
        json={"candidate_ids": [first["id"]], "reject_other_candidates": True},
        headers=headers,
    )
    assert confirmed.status_code == 201
    assert len(confirmed.json()["created_transactions"]) == 1
    repeated = await client.post("/api/imports/text", json={"text": text}, headers=headers)
    statuses = {candidate["duplicate_status"] for candidate in repeated.json()["candidates"]}
    assert "exact_duplicate" in statuses or "possible_duplicate" in statuses


@pytest.mark.asyncio
async def test_csv_import(client):
    headers = await auth_headers(client)
    content = "Дата;Сумма;Описание\n01.07.2026;349,90;Перекрёсток\n"
    response = await client.post("/api/imports/csv", files={"file": ("bank.csv", content, "text/csv")}, headers=headers)
    assert response.status_code == 201
    assert len(response.json()["candidates"]) == 1


@pytest.mark.asyncio
async def test_image_import_with_mock_ocr(client, monkeypatch):
    headers = await auth_headers(client)
    monkeypatch.setattr(ImageOcrTool, "extract_text", lambda self, content, content_type=None: "02.07.2026 Списание 220,00 RUB Метро")
    response = await client.post("/api/imports/image", files={"file": ("shot.png", b"fake", "image/png")}, headers=headers)
    assert response.status_code == 201
    assert response.json()["candidates"][0]["category"]["slug"] == "transport"
