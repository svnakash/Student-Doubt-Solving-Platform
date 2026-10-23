
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models import Question, User

questions_bp = Blueprint("questions", __name__)


def get_active_user():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None

    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        return None

    return user


def error_response(code, message, status_code):
    return jsonify({
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }), status_code


def question_response(question):
    return {
        "id": question.id,
        "student_id": question.student_id,
        "subject": question.subject,
        "title": question.title,
        "body": question.body,
        "status": question.status,
        "ai_answer": question.ai_answer,
        "created_at": question.created_at.isoformat()
        if question.created_at else None,
        "updated_at": question.updated_at.isoformat()
        if question.updated_at else None,
    }


@questions_bp.post("/")
@jwt_required()
def create_question():
    user = get_active_user()

    if user is None:
        return error_response(
            "USER_NOT_AVAILABLE",
            "This account is unavailable.",
            401,
        )

    if user.verification_status != "verified":
        return error_response(
            "VERIFICATION_REQUIRED",
            "Verify your college identity before submitting questions.",
            403,
        )

    if user.role != "student":
        return error_response(
            "STUDENT_ONLY",
            "Only students can submit questions.",
            403,
        )

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response(
            "INVALID_JSON",
            "A valid JSON object is required.",
            400,
        )

    subject = payload.get("subject")
    title = payload.get("title")
    body = payload.get("body")

    errors = {}

    if not isinstance(subject, str) or not subject.strip():
        errors["subject"] = "Subject is required."
    elif len(subject.strip()) > 120:
        errors["subject"] = "Subject must be at most 120 characters."

    if not isinstance(title, str) or not title.strip():
        errors["title"] = "Title is required."
    elif len(title.strip()) > 200:
        errors["title"] = "Title must be at most 200 characters."

    if not isinstance(body, str) or not body.strip():
        errors["body"] = "Question body is required."
    elif len(body.strip()) > 10000:
        errors["body"] = "Question body must be at most 10000 characters."

    if errors:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Please correct the submitted fields.",
                "details": errors,
            },
        }), 400

    question = Question(
        student_id=user.id,
        subject=subject.strip(),
        title=title.strip(),
        body=body.strip(),
        status="open",
    )

    try:
        db.session.add(question)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        "success": True,
        "data": question_response(question),
    }), 201


@questions_bp.get("/")
@jwt_required()
def list_questions():
    user = get_active_user()

    if user is None:
        return error_response(
            "USER_NOT_AVAILABLE",
            "This account is unavailable.",
            401,
        )

    if user.verification_status != "verified":
        return error_response(
            "VERIFICATION_REQUIRED",
            "Verify your college identity to access questions.",
            403,
        )

    query = db.select(Question)

    if user.role == "student":
        query = query.where(Question.student_id == user.id)
    elif user.role != "faculty":
        return error_response(
            "ROLE_NOT_ALLOWED",
            "Your role cannot access questions.",
            403,
        )

    subject = request.args.get("subject")
    if subject:
        query = query.where(Question.subject == subject.strip())

    status = request.args.get("status")
    if status:
        if status not in {"open", "answered", "closed"}:
            return error_response(
                "INVALID_STATUS",
                "Status must be open, answered, or closed.",
                400,
            )
        query = query.where(Question.status == status)

    query = query.order_by(Question.created_at.desc(), Question.id.desc())
    questions = db.session.execute(query.limit(100)).scalars().all()

    return jsonify({
        "success": True,
        "data": [question_response(q) for q in questions],
    }), 200


@questions_bp.get("/<int:question_id>")
@jwt_required()
def get_question(question_id):
    user = get_active_user()

    if user is None:
        return error_response(
            "USER_NOT_AVAILABLE",
            "This account is unavailable.",
            401,
        )

    if user.verification_status != "verified":
        return error_response(
            "VERIFICATION_REQUIRED",
            "Verify your college identity to access questions.",
            403,
        )

    question = db.session.get(Question, question_id)

    if question is None:
        return error_response(
            "QUESTION_NOT_FOUND",
            "The requested question was not found.",
            404,
        )

    if user.role == "student" and question.student_id != user.id:
        return error_response(
            "QUESTION_NOT_FOUND",
            "The requested question was not found.",
            404,
        )

    if user.role not in {"student", "faculty"}:
        return error_response(
            "ROLE_NOT_ALLOWED",
            "Your role cannot access questions.",
            403,
        )

    return jsonify({
        "success": True,
        "data": question_response(question),
    }), 200
