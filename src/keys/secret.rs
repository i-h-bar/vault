use base64::prelude::BASE64_STANDARD;
use pyo3::exceptions::{PyIndexError, PyValueError};
use rand::Rng;
use rayon::prelude::*;
use std::char::from_u32;
use std::fmt::{Display, Formatter};
use zerocopy::{FromBytes, Immutable, IntoBytes, KnownLayout};

use crate::keys::public::Public;
use crate::keys::{modulus, MAX_CHR};
use base64::prelude::*;
use pyo3::prelude::*;
use pyo3::types::PyType;

#[pyclass]
#[derive(IntoBytes, FromBytes, Immutable, KnownLayout)]
#[repr(C)]
pub struct Secret {
    key: [i32; 16],
    modulo: i32,
    add: i32,
    dim: i32,
}

#[pymethods]
impl Secret {
    #[new]
    pub fn new() -> Self {
        Self::default()
    }

    #[classmethod]
    pub fn from_bytes(_: &Bound<'_, PyType>, bytes_str: Vec<u8>) -> PyResult<Self> {
        Self::read_from_bytes(&bytes_str).map_err(|_| PyValueError::new_err("Invalid Bytes"))
    }

    #[classmethod]
    pub fn from_b64(py: &Bound<'_, PyType>, base64_str: String) -> PyResult<Self> {
        Self::from_bytes(
            py,
            BASE64_STANDARD
                .decode(base64_str)
                .map_err(|_| PyValueError::new_err("Could not parse b64"))?,
        )
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        self.as_bytes().to_vec()
    }

    pub fn to_b64(&self) -> String {
        BASE64_STANDARD.encode(self.as_bytes())
    }

    pub fn generate_public_key(&self) -> Public {
        let mut rng = rand::rng();
        let add = self.add;
        let mut key: [i32; 2890] = [0; 2890];
        let max_fuzz = add / 10;
        let neg_fuzz = -max_fuzz;

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

    pub fn decrypt(&self, message: &str) -> PyResult<String> {
        self._decrypt(
            &BASE64_STANDARD
                .decode(message)
                .map_err(|_| PyValueError::new_err("Could not parse b64"))?,
        )
    }
}

impl Default for Secret {
    fn default() -> Self {
        let mut rng = rand::rng();
        let mut key = [0; 16];
        let modulo = rng.random_range(11120640..111206400);
        let add: i32 = modulo / MAX_CHR;
        for num in key.iter_mut() {
            *num = rng.random_range(-4096..4096);
        }

        Self {
            key,
            modulo,
            add,
            dim: 16,
        }
    }
}

impl Secret {
    fn _decrypt(&self, message: &[u8]) -> PyResult<String> {
        if message.is_empty() {
            return Ok(String::new());
        }

        let message: &[i32] = FromBytes::ref_from_bytes(message)
            .map_err(|_| PyValueError::new_err("Could not parse bytes"))?;
        let add = self.add as f32;

        message
            .par_chunks(self.key.len() + 1)
            .map(|message_chunk| {
                let chr_answer: i32 = self
                    .key
                    .iter()
                    .zip(message_chunk)
                    .map(|(num, chunklet)| num * chunklet)
                    .sum();

                let last = message_chunk
                    .last()
                    .ok_or_else(|| PyIndexError::new_err("Could not get last chunk of message"))?;

                from_u32((modulus(last - chr_answer, self.modulo) as f32 / add).round() as u32)
                    .ok_or_else(|| PyValueError::new_err("Could not make a character from u32"))
            })
            .collect::<PyResult<String>>()
    }
}

impl Display for Secret {
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
        let secret = Secret::new();
        let public = secret.generate_public_key();

        let message = "Hello World".to_string();

        let encrypted = public.encrypt(&message);
        let decrypted = secret.decrypt(&encrypted).unwrap();

        assert_eq!(decrypted, message);
    }

    #[test]
    fn test_decryption_utf8() {
        let secret = Secret::new();
        let public = secret.generate_public_key();

        let message = "こんにちは世界".to_string();

        let encrypted = public.encrypt(&message);
        let decrypted = secret.decrypt(&encrypted).unwrap();

        assert_eq!(decrypted, message);
    }

    #[test]
    fn secret_creation() {
        let secret = Secret::new();
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
        let secret = Secret::new();
        let encrypted = String::new();
        let decrypted = secret.decrypt(&encrypted).unwrap();
        assert_eq!(decrypted, String::new());
    }
}
