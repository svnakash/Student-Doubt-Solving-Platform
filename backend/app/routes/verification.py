
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.identity_parser import parse_identity_fields
from app.services.image_validation import validate_id_card_image
from app.services.ocr import extract_text_from_image
from app.services.temporary_upload import temporary_image_copy
from app.services.verification import verify_user_against_roster
from app import limiter

verification_bp = Blueprint("verification", __name__)


@verification_bp.post("/verify-details")
@jwt_required()
def verify_details():
    # Keep the old direct-verification endpoint disabled.
    return jsonify({
        "success": False,
        "error": {
            "code": "VERIFICATION_UPLOAD_REQUIRED",
            "message": "Please use the ID-card upload endpoint.",
        },
    }), 501


@verification_bp.post("/upload")
@limiter.limit("10 per minute")
@jwt_required()
def upload_id_card():
    uploaded_file = request.files.get("id_card")

    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({
            "success": False,
            "error": {
                "code": "IMAGE_REQUIRED",
                "message": "Please upload your college ID card.",
            },
        }), 400

    is_valid, error_code = validate_id_card_image(uploaded_file)

    if not is_valid:
        return jsonify({
            "success": False,
            "error": {
                "code": error_code,
                "message": "The uploaded image is invalid. Please upload a clear JPEG or PNG image.",
            },
        }), 400

    try:
        with temporary_image_copy(uploaded_file) as image_path:
            extracted_text = extract_text_from_image(image_path)

        fields = parse_identity_fields(extracted_text)

        # Do not return or log raw OCR text or extracted identity details.
        del extracted_text

    except ValueError:
        return jsonify({
            "success": False,
            "error": {
                "code": "IMAGE_PROCESSING_FAILED",
                "message": "The image could not be processed. Please try another clear image.",
            },
        }), 400

    except Exception:
        current_app.logger.exception(
            "ID-card processing failed; sensitive content was not logged."
        )
        return jsonify({
            "success": False,
            "error": {
                "code": "OCR_UNAVAILABLE",
                "message": "Identity verification is temporarily unavailable. Please try again later.",
            },
        }), 503

    try:
        user_id = int(get_jwt_identity())

        result = verify_user_against_roster(
            user_id=user_id,
            college_id_number=fields["college_id_number"],
            extracted_name=fields["name"],
        )
    except Exception:
        current_app.logger.exception(
            "Roster verification failed; sensitive content was not logged."
        )
        return jsonify({
            "success": False,
            "error": {
                "code": "VERIFICATION_UNAVAILABLE",
                "message": "Verification is temporarily unavailable. Please try again later.",
            },
        }), 503

    if result["success"]:
        return jsonify({
            "success": True,
            "data": {
                "verification_status": result["verification_status"],
                "role": result["role"],
                "code": result["code"],
            },
        }), 200

    status_code = 429 if result["code"] == "RETRY_LIMIT_REACHED" else 422

    return jsonify({
        "success": False,
        "error": {
            "code": result["code"],
            "message": result["message"],
        },
        "data": {
            "verification_status": result.get("verification_status"),
            "attempts_remaining": result.get("attempts_remaining"),
        },
    }), status_code
