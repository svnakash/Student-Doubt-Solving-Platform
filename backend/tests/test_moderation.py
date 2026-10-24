from app import db
from app.models import Question, User

from .test_questions_api import PASSWORD, auth, create_user, set_verified_role


def test_question_rejects_inappropriate_content(app, client):
    token = create_user(client, "bad_question@example.com")
    set_verified_role(app, "bad_question@example.com")

    response = client.post(
        "/api/v1/questions/",
        headers=auth(token),
        json={
            "subject": "Math",
            "title": "Stupid question",
            "body": "Why is this so dumb?",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INAPPROPRIATE_CONTENT"


def test_answer_rejects_inappropriate_content(app, client):
    student_token = create_user(client, "moderation_student@example.com")
    set_verified_role(app, "moderation_student@example.com")

    created = client.post(
        "/api/v1/questions/",
        headers=auth(student_token),
        json={
            "subject": "Science",
            "title": "Gravity",
            "body": "Explain gravity.",
        },
    )
    question_id = created.get_json()["data"]["id"]

    faculty_token = create_user(client, "moderation_faculty@example.com")
    set_verified_role(app, "moderation_faculty@example.com", role="faculty")

    response = client.post(
        f"/api/v1/questions/{question_id}/answers",
        headers=auth(faculty_token),
        json={"body": "This is a stupid answer."},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INAPPROPRIATE_CONTENT"
