INSERT INTO rfx_template.template (
    _id,
    key,
    version,
    name,
    description,
    locale,
    channel,
    body,
    engine,
    variables_schema,
    meta_fields,
    is_active
) VALUES (
    gen_random_uuid(),
    'create-user-email',
    1,
    'Welcome Email',
    'Email template for sending welcome message to new users.',
    'en',
    'EMAIL',
    $html$<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Welcome to {{ company }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            margin: 0;
            padding: 0;
            color: #2d3436;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #0984e3, #6c5ce7);
            color: #ffffff;
            text-align: center;
            padding: 40px 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .content {
            padding: 40px 30px;
            line-height: 1.8;
        }
        .content p {
            margin-bottom: 20px;
        }
        .credentials {
            background-color: #f1f2f6;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
        }
        .credential-item {
            margin-bottom: 10px;
        }
        .credential-label {
            font-weight: bold;
            color: #636e72;
            width: 100px;
            display: inline-block;
        }
        .credential-value {
            font-family: monospace;
            background-color: #dfe6e9;
            padding: 2px 6px;
            border-radius: 4px;
            color: #d63031;
            font-weight: bold;
        }
        .button-wrapper {
            text-align: center;
            margin: 40px 0;
        }
        .button {
            background: linear-gradient(135deg, #6c5ce7, #0984e3);
            color: #ffffff !important;
            text-decoration: none;
            padding: 16px 32px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);
            transition: transform 0.2s;
            display: inline-block;
        }
        .footer {
            background-color: #f1f2f6;
            color: #636e72;
            text-align: center;
            padding: 20px;
            font-size: 13px;
        }
        .footer a {
            color: #0984e3;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{ company }}!</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{{ user_name }}</strong>,</p>
            <p>Your account has been successfully created. You can now sign in to our platform using the credentials
                below:</p>

            <div class="credentials">
                <div class="credential-item">
                    <span class="credential-label">Username:</span>
                    <span class="credential-value">{{ username }}</span>
                </div>
            </div>

            <p>To get started, please click the button below to go to your realm:</p>

            <div class="button-wrapper">
                <a href="{{ action_link }}" class="button">Go to system</a>
            </div>

            <p>If you have any questions, please don't hesitate to reach out to our support team.</p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply directly to this email.</p>
            <p>&copy; 2026 {{ company }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>$html$,
    'jinja2',
    '{}'::jsonb,
    '{"subject": "Welcome to {{ company }}"}'::jsonb,
    true
);
