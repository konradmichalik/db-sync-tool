INSERT INTO `person` (`id`, `name`)
SELECT * FROM (SELECT 4, 'Sebastian') AS tmp
WHERE NOT EXISTS (
    SELECT name FROM person WHERE name = 'Sebastian'
) LIMIT 1;