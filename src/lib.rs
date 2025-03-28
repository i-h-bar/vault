use crate::keys::public::Public;
use crate::keys::secret::Secret;
use pyo3::prelude::*;

pub mod keys;

#[pymodule]
fn lwe(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Secret>()?;
    m.add_class::<Public>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_secret_pub() {
        let _ = Secret::new();
    }

    #[test]
    fn test_public_pub() {
        let secret = Secret::new();
        let _ = secret.generate_public_key();
    }
}
