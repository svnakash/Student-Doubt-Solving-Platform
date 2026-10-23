
from app import db
from app.models import Answer, Question, User


PASSWORD = "Strong-Password-123!"


def create_user(client, email, name="Test User"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": name,
            "email": email,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200

    return response.get_json()["data"]["access_token"]


def set_verified_role(app, email, role="student"):
    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one()

        user.role = role
        user.verification_status = "verified"
        db.session.commit()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_unverified_student_cannot_create_question(app, client):
    token = create_user(client, "pending@example.com")

    response = client.post(
        "/api/v1/questions/",
        headers=auth(token),
        json={
            "subject": "Python",
            "title": "Loops",
            "body": "How does a for loop work?",
        },
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "VERIFICATION_REQUIRED"


def test_verified_student_can_create_question(app, client):
    token = create_user(client, "student@example.com")
    set_verified_role(app, "student@example.com")

    response = client.post(
        "/api/v1/questions/",
        headers=auth(token),
        json={
            "subject": "Python",
            "title": "Loops",
            "body": "How does a for loop work?",
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["subject"] == "Python"
    assert data["title"] == "Loops"
    assert data["status"] == "open"
    assert data["student_id"] is not None


def test_student_cannot_view_another_students_question(app, client):
    first_token = create_user(client, "first@example.com", "First Student")
    set_verified_role(app, "first@example.com")

    created = client.post(
        "/api/v1/questions/",
        headers=auth(first_token),
        json={
            "subject": "Math",
            "title": "Integration",
            "body": "How do I integrate x squared?",
        },
    )
    assert created.status_code == 201
    question_id = created.get_json()["data"]["id"]

    second_token = create_user(client, "second@example.com", "Second Student")
    set_verified_role(app, "second@example.com")

    response = client.get(
        f"/api/v1/questions/{question_id}",
        headers=auth(second_token),
    )

    assert response.status_code == 404


def test_student_cannot_submit_faculty_answer(app, client):
    token = create_user(client, "student2@example.com")
    set_verified_role(app, "student2@example.com")

    created = client.post(
        "/api/v1/questions/",
        headers=auth(token),
        json={
            "subject": "Python",
            "title": "Functions",
            "body": "What is a function?",
        },
    )
    question_id = created.get_json()["data"]["id"]

    response = client.post(
        f"/api/v1/questions/{question_id}/answers",
        headers=auth(token),
        json={"body": "A function is reusable code."},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "FACULTY_ONLY"


def test_verified_faculty_can_answer_question(app, client):
    student_token = create_user(client, "owner@example.com", "Question Owner")
    set_verified_role(app, "owner@example.com")

    created = client.post(
        "/api/v1/questions/",
        headers=auth(student_token),
        json={
            "subject": "Python",
            "title": "Variables",
            "body": "What is a variable?",
        },
    )
    assert created.status_code == 201
    question_id = created.get_json()["data"]["id"]

    faculty_token = create_user(client, "faculty@example.com", "Faculty Member")
    set_verified_role(app, "faculty@example.com", role="faculty")

    response = client.post(
        f"/api/v1/questions/{question_id}/answers",
        headers=auth(faculty_token),
        json={"body": "A variable stores a value."},
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["body"] == "A variable stores a value."

    with app.app_context():
        question = db.session.get(Question, question_id)
        assert question.status == "answered"

        answers = db.session.execute(
            db.select(Answer).where(Answer.question_id == question_id)
        ).scalars().all()
        assert len(answers) == 1


def test_invalid_question_payload_is_rejected(app, client):
    token = create_user(client, "invalid@example.com")
    set_verified_role(app, "invalid@example.com")

    response = client.post(
        "/api/v1/questions/",
        headers=auth(token),
        json={
            "subject": "",
            "title": "",
            "body": "",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

def test_student_can_list_only_their_own_questions(app, client):
    first_token = create_user(client, "list_first@example.com")
    set_verified_role(app, "list_first@example.com")

    created = client.post(
        "/api/v1/questions/",
        headers=auth(first_token),
        json={
            "subject": "Python",
            "title": "Loops",
            "body": "Explain loops.",
        },
    )
    assert created.status_code == 201

    second_token = create_user(client, "list_second@example.com")
    set_verified_role(app, "list_second@example.com")

    response = client.get(
        "/api/v1/questions/",
        headers=auth(second_token),
    )

    assert response.status_code == 200
    assert response.get_json()["data"] == []


def test_student_can_list_answers_to_their_own_question(app, client):
    student_token = create_user(client, "answers_owner@example.com")
    set_verified_role(app, "answers_owner@example.com")

    created = client.post(
        "/api/v1/questions/",
        headers=auth(student_token),
        json={
            "subject": "Math",
            "title": "Derivatives",
            "body": "What is a derivative?",
        },
    )
    assert created.status_code == 201
    question_id = created.get_json()["data"]["id"]

    faculty_token = create_user(client, "answers_faculty@example.com")
    set_verified_role(
        app, "answers_faculty@example.com", role="faculty"
    )

    submitted = client.post(
        f"/api/v1/questions/{question_id}/answers",
        headers=auth(faculty_token),
        json={"body": "A derivative measures a rate of change."},
    )
    assert submitted.status_code == 201

    response = client.get(
        f"/api/v1/questions/{question_id}/answers",
        headers=auth(student_token),
    )

    assert response.status_code == 200
    answers = response.get_json()["data"]
    assert len(answers) == 1
    assert answers[0]["body"] == "A derivative measures a rate of change."


def test_unverified_faculty_cannot_submit_answer(app, client):
    student_token = create_user(client, "unverified_owner@example.com")
    set_verified_role(app, "unverified_owner@example.com")

    created = client.post(
        "/api/v1/questions/",
        headers=auth(student_token),
        json={
            "subject": "Science",
            "title": "Gravity",
            "body": "Explain gravity.",
        },
    )
    assert created.status_code == 201
    question_id = created.get_json()["data"]["id"]

    faculty_token = create_user(client, "pending_faculty@example.com")
    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == "pending_faculty@example.com")
        ).scalar_one()
        user.role = "faculty"
        db.session.commit()

    response = client.post(
        f"/api/v1/questions/{question_id}/answers",
        headers=auth(faculty_token),
        json={"body": "Gravity is an attractive force."},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "VERIFICATION_REQUIRED"


def test_answer_to_nonexistent_question_returns_404(client):
    token = create_user(client, "faculty_missing@example.com")

    response = client.post(
        "/api/v1/questions/999999/answers",
        headers=auth(token),
        json={"body": "An answer."},
    )

    # This account is unverified, so authorization is checked first.
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "VERIFICATION_REQUIRED"
