use pyo3::pyclass;
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

impl Public {
    pub fn new(modulo: i32, key: [i32; 2890], add: i32, dim: i32) -> Self {
        Self {
            modulo,
            key,
            add,
            dim,
        }
    }

    pub fn encrypt(&self, message: &str) -> Vec<u8> {
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
