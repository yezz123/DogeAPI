#!/usr/bin/python3

from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hash:
    @staticmethod
    def bcrypt(password: str):
        """
        Generate a bcrypt hashed password

        Args:
            password (str): The password to hash

        Returns:
            str: The hashed password
        """
        return pwd_ctx.hash(password)

    def verify(hashed_password, plain_password):
        """
        Verify a password against a hash

        Args:
            hashed_password (bool): The hashed password
            plain_password ([type]): The plain password

        Returns:
            bool: True if the password matches, False otherwise
        """
        return pwd_ctx.verify(plain_password, hashed_password)
