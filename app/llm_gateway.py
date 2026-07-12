import os
import time
import functools
import litellm
import logfire

class LLMGatewayError(Exception):
    """Custom exception raised when LLM Gateway operations fail after all retries."""
    pass

# Rolling counter globals
TOKEN_USAGE_HISTORY = []  # List of tuples: (timestamp, tokens)
LAST_CALL_TIME = 0.0

def clean_old_token_history(now: float):
    global TOKEN_USAGE_HISTORY
    cutoff = now - 60.0
    TOKEN_USAGE_HISTORY = [item for item in TOKEN_USAGE_HISTORY if item[0] >= cutoff]

def get_recent_tokens(now: float) -> int:
    clean_old_token_history(now)
    return sum(item[1] for item in TOKEN_USAGE_HISTORY)

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
    global LAST_CALL_TIME
    
    # 1. Deliberate minimum delay pacing
    min_delay = float(os.getenv("GROQ_MIN_DELAY_SECONDS", os.getenv("GROQ_MIN_DELAY", "2.0")))
    now = time.time()
    elapsed = now - LAST_CALL_TIME
    if elapsed < min_delay:
        sleep_needed = min_delay - elapsed
        logfire.info(
            "Proactive throttling: deliberate delay of {sleep_needed:.2f}s before next Groq completion call.",
            sleep_needed=sleep_needed
        )
        time.sleep(sleep_needed)
        now = time.time()
        
    # 2. Rolling token limit proactive pacing
    tpm_limit = int(os.getenv("GROQ_TPM_LIMIT", "30000"))
    safe_ratio = float(os.getenv("GROQ_TPM_SAFE_RATIO", "0.80"))
    safe_threshold = int(tpm_limit * safe_ratio)
    
    # Estimate tokens: prompt length (chars/4) + completion estimate
    prompt_tokens_est = (len(prompt) + len(system_prompt or "")) // 4
    comp_tokens_est = int(os.getenv("GROQ_ESTIMATED_COMPLETION_TOKENS", "1024"))
    est_tokens = prompt_tokens_est + comp_tokens_est
    
    recent_tokens = get_recent_tokens(now)
    if recent_tokens + est_tokens > safe_threshold:
        needed_clearance = (recent_tokens + est_tokens) - safe_threshold
        cleared_so_far = 0
        sleep_duration = 0.0
        
        for ts, tokens in TOKEN_USAGE_HISTORY:
            cleared_so_far += tokens
            time_to_expire = (ts + 60.0) - now
            if time_to_expire > sleep_duration:
                sleep_duration = time_to_expire
            if cleared_so_far >= needed_clearance:
                break
                
        if sleep_duration > 0.0:
            sleep_duration = min(sleep_duration, 15.0)
            logfire.info(
                "Proactive throttling: rolling token limit check would likely exceed safe threshold. Sleeping for {sleep_duration:.2f}s. (Current rolling tokens: {recent_tokens}, estimated next: {next_tokens}, threshold: {safe_threshold})",
                sleep_duration=sleep_duration,
                recent_tokens=recent_tokens,
                next_tokens=est_tokens,
                safe_threshold=safe_threshold
            )
            time.sleep(sleep_duration)
            now = time.time()
            
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = litellm.completion(
        model="groq/llama-3.1-8b-instant",
        messages=messages
    )
    
    LAST_CALL_TIME = time.time()
    
    total_tokens = 0
    if hasattr(response, "usage") and response.usage:
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        logfire.info(
            "Completion token usage: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
    else:
        total_tokens = est_tokens
        
    TOKEN_USAGE_HISTORY.append((time.time(), total_tokens))
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
