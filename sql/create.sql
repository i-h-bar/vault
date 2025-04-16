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
    id       uuid  not null
        constraint password_pk
            primary key,
    user_id  uuid  not null
        constraint passwords_users_id_fk
            references users,
    name     bytea not null,
    username text,
    password text  not null,
    constraint uq_name_user_id
        unique (user_id, name)
);
