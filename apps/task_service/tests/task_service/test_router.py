import pytest
from sqlalchemy import select
from src.task_service.dependencies import get_session
from src.task_service.help_func import (
    get_inf_about_author_helper,
    send_assign_notification,
    set_author_helper,
)
from src.task_service.main import app
from src.task_service.orm_utils import check_author, set_author
from src.task_service.task_models import Tasks


@pytest.mark.asyncio
async def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "task-service"


@pytest.mark.asyncio
async def test_create_task_without_author(test_client, async_session):
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    task_data = {"title": "New Test Task", "content": "Task content", "author_id": None}

    response = test_client.post("/create_task/", json=task_data)
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"Task created: {task_data['title']}"

    await async_session.commit()

    result = await async_session.execute(select(Tasks).where(Tasks.title == task_data["title"]))
    task = result.scalar_one_or_none()
    assert task is not None
    assert task.title == task_data["title"]
    assert task.content == task_data["content"]
    assert task.author_id is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_task_with_author(test_client, async_session, mock_httpx_client):
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    task_data = {
        "title": "Task with Author",
        "content": "Task assigned to author",
        "author_id": 1,
    }

    response = test_client.post("/create_task/", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"Task created: {task_data['title']}"

    await async_session.commit()

    result = await async_session.execute(select(Tasks).where(Tasks.title == task_data["title"]))
    task = result.scalar_one_or_none()
    assert task is not None
    assert task.author_id == 1
    assert task.status == "in progress"

    assert len(mock_httpx_client.post_calls) > 0

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_task_error_handling(test_client, async_session, monkeypatch):
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    async def mock_create_task_orm(*args, **kwargs):
        raise Exception("Database error")

    monkeypatch.setattr("src.task_service.router.create_task_orm", mock_create_task_orm)

    task_data = {
        "title": "Failing Task",
        "content": "This will fail",
        "author_id": None,
    }

    response = test_client.post("/create_task/", json=task_data)
    assert response.status_code == 500
    data = response.json()
    assert "Error creating task" in data["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_set_author(test_client, async_session, test_task, mock_httpx_client):
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    author_id = 5

    response = test_client.post(
        f"/assign_a_worker/?task_id={test_task['id']}&author_id={author_id}"
    )
    assert response.status_code == 200

    await async_session.commit()

    result = await async_session.execute(select(Tasks).where(Tasks.id == test_task["id"]))
    task = result.scalar_one()
    assert task.author_id == author_id

    assert len(mock_httpx_client.post_calls) > 0

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_set_author_nonexistent_task(test_client, async_session):
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    response = test_client.post("/assign_a_worker/?task_id=99999&author_id=1")
    assert response.status_code == 404

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_inf_about_author_by_task_id(
    test_client, test_task_with_author, mock_httpx_client, async_session
):
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    print(f"Task with author: {test_task_with_author}")

    response = test_client.get(f"/get_task_by_id/?task_id={test_task_with_author['id']}")

    if response.status_code != 200:
        print(f"Error response: {response.json()}")

    assert response.status_code == 200

    assert len(mock_httpx_client.get_calls) > 0

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_inf_about_author_task_without_author(test_client, test_task, async_session):
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    response = test_client.get(f"/get_task_by_id/?task_id={test_task['id']}")
    assert response.status_code == 404
    assert "No author found for this task" in response.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_check_author_orm(async_session, test_task_with_author):
    author_id = await check_author(async_session, test_task_with_author["id"])
    assert author_id == test_task_with_author["author_id"]


@pytest.mark.asyncio
async def test_get_inf_about_author_helper_no_author(async_session, test_task):
    result = await get_inf_about_author_helper(
        session=async_session, task_id=test_task["id"], author_id=None
    )
    assert result is None


@pytest.mark.asyncio
async def test_set_author_orm(async_session, test_task):
    author_id = 10
    updated_task = await set_author(async_session, test_task["id"], author_id)
    assert updated_task is not None
    assert updated_task.author_id == author_id


@pytest.mark.asyncio
async def test_set_author_orm_nonexistent_task(async_session):
    updated_task = await set_author(async_session, 99999, 1)
    assert updated_task is None


@pytest.mark.asyncio
async def test_get_inf_about_author_helper_with_task_id(
    async_session, test_task_with_author, mock_httpx_client
):
    result = await get_inf_about_author_helper(
        session=async_session, task_id=test_task_with_author["id"], author_id=None
    )
    assert result is not None
    assert mock_httpx_client.get_calls[0]["url"].endswith(f"/{test_task_with_author['author_id']}")


@pytest.mark.asyncio
async def test_get_inf_about_author_helper_with_author_id(async_session, mock_httpx_client):
    author_id = 42
    result = await get_inf_about_author_helper(
        session=async_session, task_id=None, author_id=author_id
    )
    assert result is not None
    assert mock_httpx_client.get_calls[0]["url"].endswith(f"/{author_id}")


@pytest.mark.asyncio
async def test_set_author_helper(async_session, test_task, mock_httpx_client):
    author_id = 15
    result = await set_author_helper(
        session=async_session, task_id=test_task["id"], author_id=author_id
    )

    assert result is not None
    assert result.author_id == author_id

    assert len(mock_httpx_client.post_calls) > 0


@pytest.mark.asyncio
async def test_send_assign_notification(async_session, test_task_with_author, mock_httpx_client):
    result = await send_assign_notification(
        session=async_session,
        task_id=test_task_with_author["id"],
        author_id=None,
        provider="email",
    )

    assert result is not None
    assert len(mock_httpx_client.post_calls) > 0
    assert mock_httpx_client.post_calls[0]["json"]["provider"] == "email"


@pytest.mark.asyncio
async def test_multiple_tasks_creation(multiple_tasks):
    assert len(multiple_tasks) == 4
    assert multiple_tasks[0]["author_id"] == 1
    assert multiple_tasks[1]["author_id"] == 1
    assert multiple_tasks[2]["author_id"] == 2
    assert multiple_tasks[3]["author_id"] is None


@pytest.mark.asyncio
async def test_task_status_default(test_task):
    assert test_task["status"] == "created"


@pytest.mark.asyncio
async def test_task_with_author_status(test_task_with_author):
    assert test_task_with_author["status"] == "in progress"
