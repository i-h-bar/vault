ADD_USER = "INSERT INTO users VALUES ($1, $2, $3)"

GET_USER = "SELECT id, name, hashed_password FROM users WHERE name = $1"
