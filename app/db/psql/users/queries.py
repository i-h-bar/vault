ADD_USER = "INSERT INTO users VALUES ($1, $2, $3)"

GET_USER = "SELECT id, name, hashed_password FROM users WHERE name = $1"

GET_USER_FROM_ID = "SELECT id, name, hashed_password FROM users WHERE id = $1"
