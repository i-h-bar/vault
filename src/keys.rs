use std::fmt;
use std::fmt::Formatter;

pub mod public;
pub mod secret;

const MAX_CHR: i32 = 1114111;

#[derive(Debug)]
pub enum DecryptError {
    ByteParseError,
    SliceAccessError,
    U32ParseError,
}

impl fmt::Display for DecryptError {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        let message = match &self {
            DecryptError::ByteParseError => "byte parse error",
            DecryptError::SliceAccessError => "slice access error",
            DecryptError::U32ParseError => "u32 parse error",
        };

        write!(f, "{}", message)
    }
}

fn modulus(num: i32, modulo: i32) -> i32 {
    ((num % modulo) + modulo) % modulo
}
