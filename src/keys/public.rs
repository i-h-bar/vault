use base64::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyType;
use pyo3::{pyclass, pymethods, Bound, PyResult};
use rand::Rng;
use rayon::prelude::*;
use zerocopy::{FromBytes, Immutable, IntoBytes};

use crate::keys::modulus;

#[pyclass]
#[derive(IntoBytes, FromBytes, Immutable)]
pub struct Public {
    modulo: i32,
    key: [i32; 2890],
    add: i32,
    dim: i32,
}

#[pymethods]
impl Public {
    #[new]
    pub fn new(modulo: i32, key: [i32; 2890], add: i32, dim: i32) -> Self {
        Self {
            modulo,
            key,
            add,
            dim,
        }
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

    pub fn encrypt(&self, message: &str) -> String {
        BASE64_STANDARD.encode(self._encrypt(message))
    }
}

impl Public {
    fn _encrypt(&self, message: &str) -> Vec<u8> {
        let dim = (self.dim + 1) as usize;
        let pub_key_size = (self.dim * 10) as usize;
        let message_chars: Vec<char> = message.chars().collect();
        let mut encrypted: Vec<i32> = vec![0; dim * message_chars.len()];

        encrypted
            .par_chunks_mut(dim)
            .zip(message_chars)
            .for_each(|(chunk, chr)| {
                let mut rng = rand::rng();
                let char_num = (chr as i32) * self.add;
                for _ in 0..rng.random_range(2..5) {
                    let num = rng.random_range(0..pub_key_size);
                    let slice = (num * dim)..(num * dim) + dim;
                    self.key[slice]
                        .iter()
                        .zip(&mut *chunk)
                        .for_each(|(key_num, chunk_num)| {
                            *chunk_num += key_num;
                        })
                }

                *chunk.last_mut().expect("encrypted buffer is empty") = modulus(
                    chunk.last().expect("encrypted buffer is empty") + char_num,
                    self.modulo,
                );
            });

        encrypted.as_bytes().to_vec()
    }
}
