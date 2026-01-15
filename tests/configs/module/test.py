from db_sync_tool import sync

if __name__ == "__main__":
    sync.Sync(
        mute=True,
        yes=True,
        config={
            "type": "TYPO3",
            "target": {
                "path": "/var/www/html/tests/fixtures/www2/LocalConfiguration.php"
            },
            "origin": {
                "host": "www1",
                "user": "user",
                "password": "password",
                "path": "/var/www/html/tests/fixtures/www1/LocalConfiguration.php"
            }
    })
