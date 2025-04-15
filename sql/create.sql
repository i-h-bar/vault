create table users
(
    id              uuid not null
        constraint user_pk
            primary key,
    name            text not null,
    hashed_password bytea
);

create table passwords
(
    id       uuid not null
        constraint password_pk
            primary key,
    password text not null,
    user_id  uuid not null
        constraint passwords_users_id_fk
            references users
);
