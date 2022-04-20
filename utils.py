from pydantic import BaseModel, BaseSettings
from logging.config import dictConfig
import logging
import shutil
from pathlib import Path
import hashlib
from fastapi import UploadFile
from iroha import IrohaCrypto
from simhash import Simhash
from functools import lru_cache
import jieba


class Settings(BaseSettings):
    iroha_address: str
    account_id: str
    nextcloud_url: str
    nextcloud_username: str
    nextcloud_password: str
    private_key: str
    public_key: str
    class Config:
        env_file = ".env"


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "HyperDB"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers = {
        "HyperDB": {"handlers": ["default"], "level": LOG_LEVEL},
    }

dictConfig(LogConfig().dict())
logger = logging.getLogger("HyperDB")

@lru_cache
def get_settings():
    """
    Get the settings from the environment variables
    """
    return Settings()

def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    destination = Path(destination)
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

def trace(func):
    """
    A decorator for tracing methods' begin/end execution points
    """

    def tracer(*args, **kwargs):
        name = func.__name__
        print('\tEntering "{}"'.format(name))
        result = func(*args, **kwargs)
        print('\tLeaving "{}"'.format(name))
        return result

    return tracer


class Keypair:
    """
    Store the private key and public key in a class.
    """

    def __init__(self, private_key, public_key):
        self.private_key = private_key
        self.public_key = public_key

    def __str__(self):
        return '{} {}'.format(self.private_key, self.public_key)


class Entry:
    """
    Store the database entry in a class
    """
    def __init__(self, id, name, experiment_time, author, email, institution, environment, parameters, details, attachment, timestamp, hash=None, offset=-1):
        self.id = id
        self.name = name
        self.experiment_time = experiment_time
        self.author = author
        self.email = email
        self.institution = institution
        self.environment = environment
        self.parameters = parameters
        self.details = details
        self.attachment = attachment
        self.hash = hash
        self.offset = offset
        self.timestamp = timestamp
        self.simhash = None

    def cal_hash(self):
        """
        Return hash of data.
        """
        data = '{}{}{}{}{}{}{}{}{}{}'.format(self.name, self.experiment_time, self.author, self.email, self.institution, self.environment, self.parameters, self.details, self.attachment, self.timestamp)

        return hashlib.sha256(data.encode('utf-8'))

    def cal_simhash(self):
        data = '{};{};{};{};{};{};{};{};{};{}'.format(self.name, self.experiment_time, self.author, self.email, self.institution, self.environment, self.parameters, self.details, self.attachment,self.timestamp)
        words = jieba.lcut(data)
        return Simhash(words)

    @classmethod
    def from_tuple(cls, tuple):
        """
        Create an entry from query results.
        """
        logging.debug('from_tuple: {}'.format(tuple))
        return cls(tuple[0], tuple[1], tuple[2], tuple[3], tuple[4], tuple[5], tuple[6], tuple[7], tuple[8], tuple[9], tuple[12], tuple[10], tuple[11])