import os



class Config:
    SQLALCHEMY_DATABASE_uri = os.getenv(
        "DATABASE_URL",
        "sqilite:///mig.db"    
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False