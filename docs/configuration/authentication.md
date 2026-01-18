# Authentication

Configure SSH authentication for remote systems.

## Authentication Methods

db-sync-tool supports multiple SSH authentication methods (in order of precedence):

| Method | Security | CI/CD | Config Key |
|--------|----------|-------|------------|
| SSH Agent | High | Varies | (automatic) |
| SSH Key | High | Yes | `ssh_key` |
| Password | Low | No | `password` |
| Interactive | Low | No | (prompt) |

## SSH Agent (Recommended)

Without any configuration, db-sync-tool attempts to authenticate using your running SSH agent:

```bash
# Start SSH agent and add key
eval $(ssh-agent)
ssh-add ~/.ssh/id_rsa

# Run sync - uses agent automatically
db_sync_tool -f config.yaml
```

## SSH Key

Specify a private key file for authentication:

```yaml
origin:
  host: prod.example.com
  user: deploy
  ssh_key: /home/user/.ssh/id_rsa
```

::: tip CI/CD Usage
SSH key authentication is recommended for CI/CD pipelines. Store the key as a secret and reference it in your configuration.
:::

## Password (Not Recommended)

You can specify the password directly, but this is **not recommended** for security reasons:

```yaml
origin:
  host: prod.example.com
  user: deploy
  password: my_password  # Avoid this!
```

## Interactive Password Prompt

If no authentication method is configured, you'll be prompted to enter the password:

```
Enter SSH password for deploy@prod.example.com:
```

### Force Password Prompt

Use `--force-password` / `-fpw` to always prompt for password:

```bash
db_sync_tool -f config.yaml --force-password
```

## Jump Host Authentication

For jump host configurations, authentication cascades:

```yaml
origin:
  host: internal.example.com
  user: app_user
  ssh_key: /path/to/internal_key
  jump_host:
    host: bastion.example.com
    user: bastion_user
    # Uses origin's ssh_key if not specified
```

## Host Key Verification

SSH host keys are verified by default. If you encounter host key issues:

1. **First connection**: Accept the host key when prompted
2. **Known hosts**: Ensure the host is in `~/.ssh/known_hosts`

::: warning
Never disable host key verification in production environments.
:::

## Troubleshooting

### Permission Denied

1. Check SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
2. Verify the user has access to the remote system
3. Try connecting manually: `ssh user@host`

### Agent Connection Failed

1. Ensure SSH agent is running: `eval $(ssh-agent)`
2. Add your key: `ssh-add ~/.ssh/id_rsa`
3. Verify key is loaded: `ssh-add -l`

### Password Authentication Failed

1. Verify credentials are correct
2. Check if password authentication is enabled on the server
3. Use `--force-password` to retry with manual input
