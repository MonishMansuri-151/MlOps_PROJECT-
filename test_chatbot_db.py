import bcrypt
bcrypt.hashpw(b"monish@123", bcrypt.gensalt()).decode()