from app import db
from app.models import Question
from app.services.ai_service import generate_ai_answer_for_question

from .test_questions_api import PASSWORD, auth, create_user, set_verified_role


def test_generate_ai_answer_returns_not_configured_when_disabled(app):
    with app.app_context():
        question = Question(
            student_id=1,
            subject="Python",
            title="Loops",
            body="How does a for loop work?",
            status="open",
        )

        result = generate_ai_answer_for_question(question)

    assert result["success"] is False
    assert result["code"] == "AI_NOT_CONFIGURED"


def test_ai_answer_route_generates_and_persists_answer(app, client, monkeypatch):
    token = create_user(client, "ai@example.com")
    set_verified_role(app, "ai@example.com")

    created = client.post(
        "/api/v1/questions/",
        headers=auth(token),
        json={
            "subject": "Python",
            "title": "Functions",
            "body": "What is a function?",
        },
    )
    assert created.status_code == 201
    question_id = created.get_json()["data"]["id"]

    def fake_generate(question):
        assert question.id == question_id
        return {
            "success": True,
            "answer": "A function is a reusable block of code that performs a task.",
        }

    monkeypatch.setattr("app.routes.questions.generate_ai_answer_for_question", fake_generate)

    response = client.post(
        f"/api/v1/questions/{question_id}/generate-ai-answer",
        headers=auth(token),
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["ai_answer"] == "A function is a reusable block of code that performs a task."

    with app.app_context():
        question = db.session.get(Question, question_id)
        assert question.ai_answer == "A function is a reusable block of code that performs a task."
