import secrets
from datetime import datetime, timezone, timedelta
from pipe import Pipe
from fastapi import HTTPException, FastAPI, Request
from fastapi.responses import JSONResponse
from fluvius.data import UUID_GENR
from fluvius.error import BadRequestError
from fluvius.fastapi.helper import generate_client_token, generate_session_id
from fluvius.fastapi._meta import defaults as fastapi_config
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from . import config, logger
from .state import IDMStateManager

# ============================================================================
# Request/Response Models
# ============================================================================

class SignInRequestPayload(BaseModel):
    """Payload for requesting guest sign-in verification code"""
    email: EmailStr = Field(..., description="Guest email address")
    phone_number: Optional[str] = Field(None, max_length=50, description="Optional phone number")
    full_name: Optional[str] = Field(None, max_length=255, description="Optional full name")

class SignInPayload(BaseModel):
    """Payload for guest sign-in"""
    email: EmailStr = Field(..., description="Guest email address")

# ============================================================================
# Helper Functions
# ============================================================================

def generate_verification_code(length: int = config.VERIFICATION_CODE_LENGTH) -> str:
    """Generate a cryptographically secure numeric verification code"""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))

# ============================================================================
# Endpoint Class
# ============================================================================

class IDMGuestAuth:
    def __init__(self, app):
        self.app = app
        self.statemgr = IDMStateManager(None)

    async def send_guest_verification_email(self, email: str, code: str, full_name: Optional[str] = None) -> None:
        """
        Send verification code via email using rfx_notify domain
        """
        recipient_name = full_name or "Guest"

        # Get ttp_client from app state
        client = self.app.state.ttp_client
        if not client:
            logger.warning("[GUEST AUTH] ttp_client not available, logging code instead")
            logger.info(f"[GUEST AUTH] Verification code for {email}: {code}")
            return

        await client.send(
            "push_notification",
            command="push-notification",
            resource="notification",
            payload={
                "provider": "smtp",
                "recipients": [email],
                "subject": "Your Guest Verification Code",
                "body": f"Hello {recipient_name},\n\nYour verification code is: {code}\n\nThis code will expire in {config.VERIFICATION_TTL_MINUTES} minutes.\n\nIf you didn't request this code, please ignore this email.",
                "content_type": "TEXT",
                "meta": {},
            },
            identifier=UUID_GENR(),
            _headers={},
            _context={"source": "rfx_user"},
        )
        logger.info(f"[GUEST AUTH] Verification code sent to {email}")

    def setup_app(self):
        """Register all guest authentication endpoints"""

        @self.app.post("/auth/guest/sign-in-request")
        async def sign_in_request(request: Request, payload: SignInRequestPayload):
            try:
                email = payload.email.lower().strip()
                phone_number = payload.phone_number.strip() if payload.phone_number else None
                full_name = payload.full_name.strip() if payload.full_name else None

                # Check rate limiting - count recent requests from this email
                rate_limit_cutoff = datetime.now(timezone.utc) - timedelta(minutes=config.RATE_LIMIT_WINDOW_MINUTES)
                recent_requests = await self.statemgr.find_all(
                    "guest_verification",
                    where={
                        "email": email,
                        "created_at__gte": rate_limit_cutoff
                    }
                )

                if len(recent_requests) >= config.MAX_REQUESTS_PER_WINDOW:
                    raise BadRequestError(
                        "G200-403",
                        f"Too many verification requests. Please try again in {config.RATE_LIMIT_WINDOW_MINUTES} minutes."
                    )

                # Generate verification code
                code = generate_verification_code()
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=config.VERIFICATION_TTL_MINUTES)

                # Get client IP address
                client_ip = request.client.host if request.client else None

                # Store verification record with new schema fields
                verification_record = self.statemgr.create(
                    "guest_verification",
                    _id=UUID_GENR(),
                    method="email",
                    value=email,
                    email=email,
                    phone=phone_number,
                    code=code,
                    expires_at=expires_at,
                    verified=False,
                    verified_at=None,
                    ip_address=client_ip,
                    attempt=0
                )
                await self.statemgr.insert(verification_record)

                # Send verification email
                await self.send_guest_verification_email(email, code, full_name)

                logger.info(f"[GUEST AUTH] Verification code sent to {email}")

                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "verification_sent",
                        "email": email,
                        "expires_in": config.VERIFICATION_TTL_MINUTES * 60  # seconds
                    }
                )

            except BadRequestError as e:
                # Re-raise BadRequestError as-is
                raise
            except Exception as e:
                logger.error(f"[GUEST AUTH] Failed to send verification code: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to send verification code. Please try again later."
                )

        @self.app.post("/auth/guest/sign-in")
        async def sign_in(request: Request, code: str, payload: SignInPayload):
            """
            Verify code and establish guest session

            Args:
                code: 6-digit verification code (query parameter)
                payload: Email address in request body
            """
            try:
                email = payload.email.lower().strip()
                code = code.strip()

                # Validate code format
                if not code.isdigit() or len(code) != 6:
                    raise BadRequestError("G200-400", "Invalid code format. Code must be 6 digits.")

                # Find verification record
                verification = await self.statemgr.find_one(
                    "guest_verification",
                    where={
                        "value": email,
                        "code": code,
                        "verified": False
                    }
                )

                if not verification:
                    # Increment failed attempts
                    await self._increment_failed_attempts(email, code)
                    raise BadRequestError("G200-401", "Invalid or expired verification code")

                # Check expiration
                current_time = datetime.now(timezone.utc)
                if verification.expires_at < current_time:
                    await self.statemgr.update(verification, verified=False)
                    raise BadRequestError("G200-402", "Verification code has expired")

                # Check attempt limit
                if verification.attempt >= config.MAX_VERIFICATION_ATTEMPTS:
                    raise BadRequestError(
                        "G200-404",
                        "Too many failed attempts. Please request a new code."
                    )

                # Mark code as verified
                await self.statemgr.update(
                    verification,
                    verified=True,
                    verified_at=current_time
                )

                # Create or update guest user
                guest_user = await self.statemgr.find_one(
                    "guest_user",
                    where={"email": email}
                )

                if guest_user:
                    # Update existing user
                    await self.statemgr.update(
                        guest_user,
                        last_active_at=current_time,
                        email_verified=True
                    )
                else:
                    # Create new guest user
                    session_id = generate_session_id(request.session)
                    guest_user = self.statemgr.create(
                        "guest_user",
                        _id=UUID_GENR(),
                        email=email,
                        phone=verification.phone,
                        full_name=verification.email or "Guest",
                        session_id=session_id,
                        email_verified=True,
                        last_active_at=current_time
                    )
                    await self.statemgr.insert(guest_user)

                # Create guest payload (mimic Keycloak token structure)
                guest_payload = {
                    "guest_id": str(guest_user._id),
                    "email": email,
                    "fullname": verification.email or "Guest",
                    "phone": verification.phone,
                    "session_id": generate_session_id(request.session),
                    "client_token": generate_client_token(request.session),
                    "verified_at": current_time.isoformat()
                }

                # Regenerate session to prevent session fixation
                old_data = dict(request.session)
                request.session.clear()
                request.session.update(old_data)

                # Remove regular user session if exists
                request.session.pop(fastapi_config.SES_USER_FIELD, None)

                # Store guest session
                request.session[fastapi_config.SES_GUEST_FIELD] = guest_payload

                # Create response
                session_expires_at = current_time + timedelta(hours=config.GUEST_SESSION_TTL_HOURS)
                response = JSONResponse(
                    status_code=200,
                    content={
                        "status": "authenticated",
                        "guest_id": str(guest_user._id),
                        "email": email,
                        "session_expires_at": session_expires_at.isoformat()
                    }
                )

                # Set secure cookie
                response.set_cookie(
                    fastapi_config.SES_ID_TOKEN_FIELD,
                    "guest",
                    httponly=True,
                    secure=fastapi_config.COOKIE_HTTPS_ONLY,
                    samesite=fastapi_config.COOKIE_SAME_SITE_POLICY,
                    max_age=config.GUEST_SESSION_TTL_HOURS * 3600
                )

                logger.info(f"[GUEST AUTH] Guest user {email} signed in successfully")
                return response

            except BadRequestError:
                raise
            except Exception as e:
                logger.error(f"[GUEST AUTH] Sign-in failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Sign-in failed. Please try again later."
                )

        return self.app

    async def _increment_failed_attempts(self, email: str, code: str):
        """Increment attempt counter for failed verification"""
        verification = await self.statemgr.find_one(
            "guest_verification",
            where={"value": email, "code": code}
        )

        if verification:
            await self.statemgr.update(
                verification,
                attempt=verification.attempt + 1
            )


# ============================================================================
# Configuration
# ============================================================================

@Pipe
def configure_guest_auth(app: FastAPI):
    """Configure guest authentication endpoints"""
    guest_auth = IDMGuestAuth(app)
    app = guest_auth.setup_app()
    return app
