
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models import Answer, Question, User

answers_bp = Blueprint("answers", __name__)


def error_response(code, message, status_code):
    return jsonify({
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }), status_code


def get_active_user():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None

    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        return None

    return user


def answer_response(answer):
    return {
        "id": answer.id,
        "question_id": answer.question_id,
        "faculty_id": answer.faculty_id,
        "body": answer.body,
        "created_at": (
            answer.created_at.isoformat()
            if answer.created_at else None
        ),
    }


@answers_bp.post("/<int:question_id>/answers")
@jwt_required()
def create_answer(question_id):
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
            "Verify your college identity first.",
            403,
        )

    if user.role != "faculty":
        return error_response(
            "FACULTY_ONLY",
            "Only verified faculty can submit answers.",
            403,
        )

    question = db.session.get(Question, question_id)

    if question is None:
        return error_response(
            "QUESTION_NOT_FOUND",
            "The requested question was not found.",
            404,
        )

    if question.status == "closed":
        return error_response(
            "QUESTION_CLOSED",
            "This question is closed and cannot receive answers.",
            409,
        )

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return error_response(
            "INVALID_JSON",
            "A valid JSON object is required.",
            400,
        )

    body = payload.get("body")

    if not isinstance(body, str) or not body.strip():
        return error_response(
            "VALIDATION_ERROR",
            "Answer body is required.",
            400,
        )

    if len(body.strip()) > 10000:
        return error_response(
            "VALIDATION_ERROR",
            "Answer body must be at most 10000 characters.",
            400,
        )

    answer = Answer(
        question_id=question.id,
        faculty_id=user.id,
        body=body.strip(),
    )

    try:
        db.session.add(answer)
        question.status = "answered"
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        "success": True,
        "data": answer_response(answer),
    }), 201


@answers_bp.get("/<int:question_id>/answers")
@jwt_required()
def list_answers(question_id):
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
            "Verify your college identity first.",
            403,
        )

    question = db.session.get(Question, question_id)

    if question is None:
        return error_response(
            "QUESTION_NOT_FOUND",
            "The requested question was not found.",
            404,
        )

    if user.role == "student":
        if question.student_id != user.id:
            return error_response(
                "QUESTION_NOT_FOUND",
                "The requested question was not found.",
                404,
            )
    elif user.role != "faculty":
        return error_response(
            "ROLE_NOT_ALLOWED",
            "Your role cannot access answers.",
            403,
        )

    answers = db.session.execute(
        db.select(Answer)
        .where(Answer.question_id == question.id)
        .order_by(Answer.created_at.asc(), Answer.id.asc())
    ).scalars().all()

    return jsonify({
        "success": True,
        "data": [answer_response(answer) for answer in answers],
    }), 200
