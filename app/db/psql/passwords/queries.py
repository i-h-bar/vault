# ruff: noqa: S105

INSERT_PASSWORD = "INSERT INTO passwords (id, user_id, username, password, name) VALUES ($1, $2, $3, $4, $5)"
GET_PASSWORD = "SELECT username, password FROM passwords where name = $1 and user_id = $2"
