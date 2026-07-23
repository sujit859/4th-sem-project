from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

def generate_token(user):
    signer = TimestampSigner()
    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'username': user.username
    }
    return signer.sign_object(payload)

def verify_token(token, max_age=86400):  # 24 hours expiration
    signer = TimestampSigner()
    try:
        return signer.unsign_object(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
