import time
import functools
import litellm
import logfire

class LLMGatewayError(Exception):
    """Custom exception raised when LLM Gateway operations fail after all retries."""
    pass

def with_retry(max_retries=3, backoffs=[1, 2, 4]):
    """
    Decorator that retries a function call up to max_retries times
    with exponential backoff on failure.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            func_name = func.__name__
            with logfire.span("LLM API call: {func_name}", func_name=func_name):
                for attempt in range(max_retries + 1):
                    try:
                        res = func(*args, **kwargs)
                        if attempt > 0:
                            logfire.info("LLM call {func_name} succeeded on attempt {attempt_num}", func_name=func_name, attempt_num=attempt + 1)
                        return res
                    except Exception as e:
                        last_exc = e
                        if attempt < max_retries:
                            sleep_time = backoffs[min(attempt, len(backoffs) - 1)]
                            logfire.warn(
                                "LLM attempt {attempt_num} failed: {err}. Retrying in {sleep_time}s...", 
                                attempt_num=attempt + 1, 
                                err=str(e), 
                                sleep_time=sleep_time
                            )
                            time.sleep(sleep_time)
                
                logfire.error("LLM call {func_name} failed after all {max_attempts} attempts. Final error: {err}", func_name=func_name, max_attempts=max_retries+1, err=str(last_exc))
                raise LLMGatewayError(f"LLM operation failed after {max_retries + 1} attempts: {last_exc}") from last_exc
        return wrapper
    return decorator

@with_retry()
def generate_embedding(text: str) -> list[float]:
    """
    Generates embedding vector for the given text using Gemini's gemini-embedding-001 model via LiteLLM.
    Reads GEMINI_API_KEY from environment variables.
    Note: Switch to gemini-embedding-001 as text-embedding-004 is deprecated/unsupported on this API account.
    """
    response = litellm.embedding(
        model="gemini/gemini-embedding-001",
        input=[text]
    )
    if 'usage' in response and response['usage']:
        usage = response['usage']
        logfire.info(
            "Embedding token usage: prompt={prompt_tokens}, total={total_tokens}",
            prompt_tokens=usage.get("prompt_tokens"),
            total_tokens=usage.get("total_tokens")
        )
    return response['data'][0]['embedding']

@with_retry()
def generate_completion(prompt: str, system_prompt: str = None) -> str:
    """
    Generates text completion using Groq's llama-3.1-8b-instant model via LiteLLM.
    Reads GROQ_API_KEY from environment variables.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = litellm.completion(
        model="groq/llama-3.1-8b-instant",
        messages=messages
    )
    if hasattr(response, "usage") and response.usage:
        logfire.info(
            "Completion token usage: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}",
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )
    return response.choices[0].message.content or ""

def batch_generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings for a batch of texts.
    Processes sequential calls with internal retry logic.
    Note: true batching could be added later if the embedding API supports it natively.
    """
    results = []
    for text in texts:
        results.append(generate_embedding(text))
    return results
