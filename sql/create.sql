create table users
(
    id              uuid not null
        constraint user_pk
            primary key,
    name            text not null,
    hashed_password bytea
);
