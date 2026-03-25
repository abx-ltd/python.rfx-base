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
    'org-invitation-default',
    1,
    'Organization Invitation',
    'Email template for inviting users to an organization.',
    'en',
    'EMAIL',
    $html$<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Invitation to join {{ organization_name }}</title>
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
            background: linear-gradient(135deg, #00b894, #0984e3);
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
        .invitation-box {
            background-color: #f1f2f6;
            border-left: 4px solid #00b894;
            padding: 20px;
            margin: 30px 0;
            font-style: italic;
            color: #636e72;
        }
        .button-wrapper {
            text-align: center;
            margin: 40px 0;
        }
        .button {
            color: #ffffff !important;
            text-decoration: none;
            padding: 16px 32px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 18px;
            display: inline-block;
            margin: 10px;
            min-width: 150px;
        }
        .button-accept {
            background: linear-gradient(135deg, #00b894, #00cec9);
            box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
        }
        .button-reject {
            background: #dfe6e9;
            color: #636e72 !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        }
        .expiry-note {
            text-align: center;
            color: #b2bec3;
            font-size: 14px;
            margin-top: 20px;
        }
        .footer {
            background-color: #f1f2f6;
            color: #636e72;
            text-align: center;
            padding: 20px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>You're Invited!</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>You have been invited to join <strong>{{ organization_name }}</strong> on our platform.</p>

            {% if message %}
            <div class="invitation-box">
                "{{ message }}"
            </div>
            {% endif %}

            <p>To accept this invitation and access the organization dashboard, please click the button below:</p>

            <div class="button-wrapper">
                <a href="{{ accept_link }}" class="button button-accept">Accept Invitation</a>
                <a href="{{ reject_link }}" class="button button-reject">Decline</a>
            </div>

            <p class="expiry-note">
                This invitation will expire in {{ duration_days }} days.
            </p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply directly to this email.</p>
            <p>&copy; 2026 {{ organization_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>$html$,
    'jinja2',
    '{}'::jsonb,
    '{"subject": "Invitation to join {{ organization_name }}"}'::jsonb,
    true
);
