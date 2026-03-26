INSERT INTO rfx_user.ref__action (_id, _created, key, display) VALUES
(gen_random_uuid(), now(), 'VERIFY_EMAIL', 'Verify Email'),
(gen_random_uuid(), now(), 'UPDATE_PASSWORD', 'Update Password'),
(gen_random_uuid(), now(), 'PASSWORD_CHANGE', 'Change Password'),
(gen_random_uuid(), now(), 'CONFIGURE_TOTP', 'Configure MFA'),
(gen_random_uuid(), now(), 'UPDATE_PROFILE', 'Update Profile'),
(gen_random_uuid(), now(), 'TERMS_AND_CONDITIONS', 'Accept Terms')
ON CONFLICT (key) DO NOTHING;
