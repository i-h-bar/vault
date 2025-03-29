pub mod public;
pub mod secret;

const MAX_CHR: i32 = 1114111;

fn modulus(num: i32, modulo: i32) -> i32 {
    ((num % modulo) + modulo) % modulo
}
