import os
import time
import random
import json
import re
from google import genai
from mistralai import Mistral
from config import (
    FLASH_VLM_SETTINGS,
    SOTA_VLM_SETTINGS,
    LLM_SETTINGS,
    VLM_SETTINGS_MIS,
    LLM_SETTINGS_MIS,
)
import llm_utils.gemini_message as gemini_message


class BaseVLMClient:
    """
    Abstract base class defining VLM client interface.
    """

    def __init__(self):
        self.provider = None
        raise NotImplementedError
    def decide_plan(self, msg, response_format=None, model_index = 0):
        raise NotImplementedError
    def infer(
        self, msg, response_format=None, model_index=0
    ):  # model index 0 for llm, 1 for vlm, 2 for sota vlm
        raise NotImplementedError


class GeminiVLMClient(BaseVLMClient):
    def __init__(self):
        api_key = os.environ.get("GENAI_API_KEY")
        if not api_key:
            raise RuntimeError("GENAI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)
        self.flash_vlm = FLASH_VLM_SETTINGS["model_name"]
        self.flash_vlm_max_tokens = FLASH_VLM_SETTINGS["max_tokens"]
        self.flash_vlm_temperature = FLASH_VLM_SETTINGS["temperature"]
        self.sota_vlm = SOTA_VLM_SETTINGS["model_name"]
        self.sota_vlm_max_tokens = SOTA_VLM_SETTINGS["max_tokens"]
        self.sota_vlm_temperature = SOTA_VLM_SETTINGS["temperature"]
        self.llm = LLM_SETTINGS["model_name"]
        self.llm_max_tokens = LLM_SETTINGS["max_tokens"]
        self.llm_temperature = LLM_SETTINGS["temperature"]
        self.provider = "GEMINI"


    def decide_plan(self, msg, response_format=None, model_index=0):
        max_retries = 5
        base_delay = 2  # Base delay in seconds

        for attempt in range(max_retries):
            try:
                if response_format is None:
                    chat_response = self.client.models.generate_content(
                        model=self.flash_vlm if model_index <= 1 else self.sota_vlm,
                        contents=msg,
                    )
                    raw_text = chat_response.text
                    return raw_text
                else:
                    chat_response = self.client.models.generate_content(
                        model=self.flash_vlm if model_index <= 1 else self.sota_vlm,
                        contents=msg,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": response_format,
                        },
                    )
                    return chat_response.text

            except Exception as e:
                # Check if it's a rate limit error or another retryable API error
                error_str = str(e).lower()
                if (
                    "rate limit" in error_str
                    or "too many requests" in error_str
                    or "service unavailable" in error_str # Added for more robustness
                ):
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        # Calculate exponential backoff with jitter
                        delay = base_delay * (2**attempt) + random.uniform(0, 1)
                        print(
                            f"API limit exceeded. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        print(f"Failed after {max_retries} attempts due to API limits.")
                        raise
                else:
                    # Handle other non-retryable errors immediately
                    print(f"An unexpected API error occurred: {e}")
                    raise

        # This line would be reached if the loop completes without returning or raising,
        # which indicates a logic error. We raise an error to handle it.
        raise RuntimeError("Failed to get a response after all retries.")
    def infer(self, msg, response_format=None, model_index=0) -> dict:
        max_retries = 5
        base_delay = 2  # Base delay in seconds

        for attempt in range(max_retries):
            try:
                if response_format is None:
                    chat_response = self.client.models.generate_content(
                        model=self.flash_vlm if model_index <= 1 else self.sota_vlm,
                        contents=msg,
                    )
                    raw_text = chat_response.text

                    # Clean the string to extract the JSON
                    # This will find the content between the first '{' and the last '}'
                    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    return json.loads(match.group(0))
                else:
                    chat_response = self.client.models.generate_content(
                        model=self.flash_vlm if model_index <= 1 else self.sota_vlm,
                        contents=msg,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": response_format,
                        },
                    )
                    return json.loads(chat_response.text)

            except Exception as e:
                # Check if it's a rate limit error or another retryable API error
                error_str = str(e).lower()
                if (
                    "rate limit" in error_str
                    or "too many requests" in error_str
                    or "service unavailable" in error_str # Added for more robustness
                ):
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        # Calculate exponential backoff with jitter
                        delay = base_delay * (2**attempt) + random.uniform(0, 1)
                        print(
                            f"API limit exceeded. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        print(f"Failed after {max_retries} attempts due to API limits.")
                        raise
                else:
                    # Handle other non-retryable errors immediately
                    print(f"An unexpected API error occurred: {e}")
                    raise

        # This line would be reached if the loop completes without returning or raising,
        # which indicates a logic error. We raise an error to handle it.
        raise RuntimeError("Failed to get a response after all retries.")