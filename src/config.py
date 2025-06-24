import os

from dotenv import load_dotenv, find_dotenv
from openai import AsyncOpenAI

from src import logging
import os, logging

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.example")

logger = logging.getLogger(__name__)


WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MONGODB_URL = os.getenv("MONGODB_URL")

VECTOR_STORE_ID = "vs_685a7c02c9f881919e2efc5466346f87"




if not all(
    [WHATSAPP_TOKEN, VERIFY_TOKEN, OPENAI_API_KEY, PHONE_NUMBER_ID, MONGODB_URL]
):
    logger.error("Missing required environment variables")
    raise ValueError("Please set all required environment variables")


async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
for var in [WHATSAPP_TOKEN, VERIFY_TOKEN, OPENAI_API_KEY, PHONE_NUMBER_ID, MONGODB_URL]:
    if not var:
        logging.error("Missing %s", var)
        raise ValueError("Please set all required environment variables")