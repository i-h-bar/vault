use std::char::from_u32;
use std::fmt::{Display, Formatter};
use pyo3::exceptions;
use pyo3::exceptions::{PyIndexError, PyTypeError, PyValueError};
use rand::Rng;
use rayon::prelude::*;
use zerocopy::{FromBytes, Immutable, IntoBytes};

use crate::keys::public::Public;
use crate::keys::{
    modulus,
    DecryptError::{self, ByteParseError, SliceAccessError, U32ParseError},
    MAX_CHR,
};
use pyo3::prelude::*;

#[pyclass]
#[derive(IntoBytes, FromBytes, Immutable)]
pub struct Secret16 {
    key: [i32; 16],
    modulo: i32,
    add: i32,
    dim: i32,
}

#[pymethods]
impl Secret16 {
    #[new]
    pub fn new() -> Self {
        let mut rng = rand::rng();
        let mut key = [0; 16];
        let modulo = rng.random_range(11120640..111206400);
        let add: i32 = modulo / MAX_CHR;
        for i in 0..16 {
            key[i] = rng.random_range(-4096..4096);
        }

        Secret16 {
            key,
            modulo,
            add,
            dim: 16,
        }
    }

    pub fn generate_public_key(&self) -> Public {
        let mut rng = rand::rng();
        let add = self.add;
        let mut key: [i32; 2890] = [0; 2890];
        let max_fuzz = add / 10;
        let neg_fuzz = -1 * max_fuzz;

        key.chunks_mut((self.dim + 1) as usize).for_each(|chunk| {
            let answer: i32 = self
                .key
                .iter()
                .zip(&mut *chunk)
                .map(|(key_num, chunklet)| {
                    let num = rng.random_range(-4096..4096);
                    *chunklet = num;
                    key_num * num
                })
                .sum();

            *chunk
                .last_mut()
                .expect("Attempted `.last_mut()` on an empty chunk") =
                modulus(answer + rng.random_range(neg_fuzz..max_fuzz), self.modulo);
        });

        Public::new(self.modulo, key, add, self.dim)
    }

    pub fn decrypt(&self, message: &[u8]) -> PyResult<String> {
        if message.is_empty() {
            return Ok(String::new());
        }

        let message: &[i32] = FromBytes::ref_from_bytes(message)
            .map_err(|_| PyValueError::new_err("Could not parse bytes"))?;
        let add = self.add as f32;

        Ok(message
            .par_chunks(self.key.len() + 1)
            .map(|message_chunk| {
                let chr_answer: i32 = self
                    .key
                    .iter()
                    .zip(message_chunk)
                    .map(|(num, chunklet)| num * chunklet)
                    .sum();

                let last = message_chunk.last().ok_or_else(|| PyIndexError::new_err("Could not get last chunk of message"))?;
                Ok(
                    from_u32((modulus(last - chr_answer, self.modulo) as f32 / add).round() as u32)
                        .ok_or_else(|| PyValueError::new_err("Could not make a character from u32"))?,
                )
            })
            .collect::<PyResult<String>>()?)
    }
}

impl Display for Secret16 {
    fn fmt(&self, f: &mut Formatter) -> std::fmt::Result {
        let output = format!("Secret {{ {:?} }}", self.key)
            .replace("[", "")
            .replace("]", "");

        write!(f, "{}", output)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decryption() {
        let secret = Secret16::new();
        let public = secret.generate_public_key();

        let message = "Hello World".to_string();

        let encrypted = public.encrypt(&message);
        let decrypted = secret.decrypt(&encrypted).unwrap();

        assert_eq!(decrypted, message);
    }

    #[test]
    fn test_decryption_utf8() {
        let secret = Secret16::new();
        let public = secret.generate_public_key();

        let message = "こんにちは世界".to_string();

        let encrypted = public.encrypt(&message);
        let decrypted = secret.decrypt(&encrypted).unwrap();

        assert_eq!(decrypted, message);
    }

    #[test]
    fn secret_creation() {
        let secret = Secret16::new();
        assert_eq!(secret.key.len(), 16);

        let mod_range = 11120640..111206400;
        assert!(mod_range.contains(&secret.modulo));

        let key_range = -32768..32768;
        for num in secret.key.iter() {
            assert!(key_range.contains(num));
        }
    }

    #[test]
    fn decrypt_empty_message() {
        let secret = Secret16::new();
        let encrypted: [u8; 0] = [];
        let decrypted = secret.decrypt(&encrypted).unwrap();
        assert_eq!(decrypted, String::new());
    }
}
