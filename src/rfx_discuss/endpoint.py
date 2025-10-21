def register_webhook_routes(app):
    async def verify_linear_webhook(request):
        """Verify Linear webhook signature"""
        hmac_signature = request.headers.get("X-Linear-Signature")
        
        # Implement verification logic here (e.g., HMAC signature check)
        return True
    app.route('/webhooks/linear', methods=['POST'])
    async def linear_webhook(request):
        if not await verify_linear_webhook(request):
            return {"error": "Invalid webhook signature"}, 403
        """Endpoint to receive Linear webhooks"""
        logger.info("Received Linear webhook")
        data = await request.json()
        logger.debug(f"Webhook payload: {data}")
    return app