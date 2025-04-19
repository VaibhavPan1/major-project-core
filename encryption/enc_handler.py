


class CryptoVault:
    def __init__(self):
        pass

    # RSA Key Generation (for Judge and Lawyer)
    def generate_rsa_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem, public_pem

    # Encrypt File for Multiple Recipients
    def encrypt_file(self, file_path, recipient_public_keys: dict):
        aes_key = os.urandom(32)  # AES-256 key
        iv = os.urandom(16)       # AES IV

        # Read file
        with open(file_path, 'rb') as f:
            plaintext = f.read()

        # Pad plaintext
        padding_len = 16 - (len(plaintext) % 16)
        padded_plaintext = plaintext + bytes([padding_len] * padding_len)

        # Encrypt file with AES
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

        # Encrypt AES key for each recipient
        encrypted_keys = {}
        for user_id, pub_pem in recipient_public_keys.items():
            public_key = serialization.load_pem_public_key(pub_pem)
            encrypted_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            encrypted_keys[user_id] = encrypted_key

        return ciphertext, iv, encrypted_keys

    # Decrypt file using private key and encrypted AES key
    def decrypt_file(self, ciphertext, iv, encrypted_key, private_key_pem):
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)

        # Decrypt AES key
        aes_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Decrypt file
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Unpad
        padding_len = padded_plaintext[-1]
        plaintext = padded_plaintext[:-padding_len]

        return plaintext