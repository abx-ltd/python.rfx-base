# Alembic Migration Guide

## Schema-Specific Migrations

This project supports generating migrations for specific database schemas to keep migrations organized and focused.

### Available Schemas

- **`user`** - User profile management (`rfx_user` schema)
- **`policy`** - Policy and permissions (`rfx_policy` schema)
- **`message`** - Messaging and notifications (`rfx_message` schema)
- **`all`** - All schemas (default)

### Quick Start Commands

All commands use the `just` task runner. Run `just --list` to see all available commands.

#### Generate Migration (Autogenerate)

```bash
# For all schemas (default)
just mig-autogen "add new field to user table"

# For specific schema
just mig-autogen "add user preferences" user

# For multiple schemas
just mig-autogen "update user and message tables" user,message
```

#### Apply Migrations

```bash
# Upgrade to latest (all schemas)
just mig-upgrade

# Upgrade specific schema
just mig-upgrade head user

# Upgrade to specific revision
just mig-upgrade abc123 user
```

#### Rollback Migrations

```bash
# Rollback one step (all schemas)
just mig-downgrade

# Rollback one step for specific schema
just mig-downgrade -1 user

# Rollback to specific revision
just mig-downgrade abc123 user
```

#### Other Useful Commands

```bash
# Check current migration version
just mig-current

# View migration history
just mig-history

# Check for differences between DB and models
just mig-check

# Check specific schema
just mig-check user

# Create empty migration
just mig-revision "custom migration" user
```

### Direct Alembic Commands

If you need more control, you can use alembic directly with the `ALEMBIC_SCHEMA_FILTER` environment variable:

```bash
# Generate migration for user schema only
ALEMBIC_SCHEMA_FILTER=user alembic -c alembic/alembic.ini revision --autogenerate -m "message"

# Generate for multiple schemas
ALEMBIC_SCHEMA_FILTER=user,message alembic -c alembic/alembic.ini revision --autogenerate -m "message"

# All schemas (default)
alembic -c alembic/alembic.ini revision --autogenerate -m "message"
```

### Best Practices

1. **Use specific schemas when possible** - This keeps migrations focused and easier to review
2. **Clear migration messages** - Use descriptive messages that explain what changed
3. **Review generated migrations** - Always review auto-generated migrations before committing
4. **Test migrations** - Test both upgrade and downgrade paths
5. **One logical change per migration** - Keep migrations atomic and focused

### Migration Naming Convention

Use clear, descriptive messages:
- ✅ `"add username index to user table"`
- ✅ `"add message_template table"`
- ❌ `"update"`
- ❌ `"fix"

### Examples

```bash
# Example 1: Adding a new field to user profile
just mig-autogen "add preferred_language to profile" user

# Example 2: Creating new message template table
just mig-autogen "create message_template table" message

# Example 3: Updating multiple schemas
just mig-autogen "add audit timestamps" user,policy,message

# Example 4: Apply all pending migrations for user schema
just mig-upgrade head user

# Example 5: Check what would change without generating migration
just mig-check user
```

### Troubleshooting

**Problem**: Migration includes tables from other schemas
**Solution**: Make sure to specify the schema filter: `just mig-autogen "message" user`

**Problem**: No changes detected
**Solution**:
1. Check that your model changes are imported in `rfx_schema/_schema.py`
2. Verify the schema name matches: `user`, `policy`, or `message`
3. Try `just mig-check user` to see if changes are detected

**Problem**: Want to see what schemas are being used
**Solution**: Check the alembic logs - they will show which schemas are active

### Advanced: Adding New Schemas

To add a new schema to the migration system:

1. Add schema name to `rfx_base/_meta/defaults.py`
2. Update `ALL_SCHEMAS` dict in `alembic/env.py`
3. Add the schema constant to the mapping

Example:
```python
# In alembic/env.py
ALL_SCHEMAS = {
    'user': base_config.RFX_USER_SCHEMA,
    'policy': base_config.RFX_POLICY_SCHEMA,
    'message': base_config.RFX_MESSAGE_SCHEMA,
    'billing': base_config.RFX_BILLING_SCHEMA,  # New schema
}
```
