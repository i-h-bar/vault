ADD_USER = 'INSERT INTO "user" VALUES ($1, $2, $3)'

GET_USER = 'SELECT id, name, hashed_password FROM "user" WHERE name = $1'
