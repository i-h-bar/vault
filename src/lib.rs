pub mod keys;



#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_secret_pub() {
        let _ = keys::secret::Secret16::new();
    }

    #[test]
    fn test_public_pub() {
        let secret = keys::secret::Secret16::new();
        let _ = secret.generate_public_key();
    }
}
