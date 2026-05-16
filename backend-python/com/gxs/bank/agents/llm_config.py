"""
LLM configuration for CrewAI agents.

Priority chain:
  1. AWS Bedrock (DeepSeek V3.2 via Converse API) → primary for hackathon
  2. CrewAI + ANTHROPIC_API_KEY                    → full multi-agent orchestration
  3. CrewAI + OPENAI_API_KEY                       → full multi-agent orchestration
  4. Direct anthropic SDK                          → single-call LLM mode
  5. Direct openai SDK                             → single-call LLM mode
  6. No key / no SDK                               → deterministic Python fallback

Available Bedrock models (us-west-2):
  - deepseek.v3.2                     → DeepSeek V3.2 (primary chat model)
  - deepseek.v3-v1:0                  → DeepSeek V3.1
  - qwen.qwen3-235b-a22b-2507-v1:0   → Qwen3 235B MoE (fallback)
  - qwen.qwen3-32b-v1:0              → Qwen3 32B dense
  - nvidia.nemotron-super-3-120b      → Nemotron 120B
  - amazon.titan-embed-text-v2:0      → Titan Embeddings V2 (for ChromaDB)
"""

import json
import os
import traceback

# Optional retry helper (tenacity). We fall back to no-retry if tenacity isn't installed.
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    TENACITY_AVAILABLE = True
except Exception:
    TENACITY_AVAILABLE = False

try:
    from botocore.config import Config as BotoConfig
    import botocore.exceptions as botocore_exceptions
    BOTOCORE_AVAILABLE = True
except Exception:
    BOTOCORE_AVAILABLE = False

# ── AWS Bedrock availability ────────────────────────────────────────────────
BEDROCK_AVAILABLE = False
try:
    import boto3  # noqa: F401
    BEDROCK_AVAILABLE = True
except ImportError:
    pass

# ── CrewAI availability (requires Python ≤ 3.13) ────────────────────────────
CREWAI_AVAILABLE = False
try:
    import crewai  # noqa: F401
    CREWAI_AVAILABLE = True
except ImportError:
    pass

# ── Direct SDK availability (works on Python 3.14+) ─────────────────────────
ANTHROPIC_AVAILABLE = False
try:
    import anthropic  # noqa: F401
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

OPENAI_AVAILABLE = False
try:
    import openai  # noqa: F401
    OPENAI_AVAILABLE = True
except ImportError:
    pass


# ── Bedrock model configuration ─────────────────────────────────────────────
# DeepSeek V3.2 is the primary model; override via env var if needed
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "deepseek.v3.2")
BEDROCK_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")

# Fallback model if primary fails (Qwen3 235B MoE)
BEDROCK_FALLBACK_MODEL = os.getenv("BEDROCK_FALLBACK_MODEL", "qwen.qwen3-235b-a22b-2507-v1:0")


def _has_bedrock_credentials() -> bool:
    """Check if AWS credentials are set (via env vars or IAM role)."""
    return bool(os.getenv("AWS_ACCESS_KEY_ID")) or bool(os.getenv("AWS_ROLE_ARN"))


def _get_bedrock_client():
    """Create and return a boto3 Bedrock Runtime client."""
    if not BEDROCK_AVAILABLE:
        return None
    try:
        # Configure network timeouts if botocore is available
        connect_timeout = int(os.getenv("LLM_CONNECT_TIMEOUT", "5"))
        read_timeout = int(os.getenv("LLM_READ_TIMEOUT", "30"))
        retry_attempts = int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))

        session = boto3.Session(
            region_name=BEDROCK_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )

        if BOTOCORE_AVAILABLE:
            config = BotoConfig(connect_timeout=connect_timeout, read_timeout=read_timeout)
            return session.client("bedrock-runtime", config=config)
        else:
            return session.client("bedrock-runtime")
    except Exception as e:
        print(f"[LLM CONFIG] Bedrock client creation failed: {e}", flush=True)
        if os.getenv("DEBUG_LLM_ERRORS", "false").lower() in {"1", "true", "yes"}:
            traceback.print_exc()
        return None


def _bedrock_converse(prompt: str, system: str = "", model_id: str = "") -> str:
    """
    Call a Bedrock model using the Converse API (provider-agnostic).
    Works with DeepSeek, Qwen, Nvidia, Google, and all other Bedrock models.
    Returns the text response, or empty string on failure.
    """
    client = _get_bedrock_client()
    if not client:
        return ""

    target_model = model_id or BEDROCK_MODEL_ID
    system_prompt = system or "You are a helpful financial advisor for gig economy workers at GXS Bank."

    # Retry wrapper (no-op if tenacity not installed)
    def _call():
        response = client.converse(
            modelId=target_model,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.3,
            },
        )
        return response

    try:
        if TENACITY_AVAILABLE:
            @retry(reraise=True,
                   stop=stop_after_attempt(int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))),
                   wait=wait_exponential(multiplier=1, min=1, max=10),
                   retry=retry_if_exception_type(Exception))
            def _call_with_retry():
                return _call()

            response = _call_with_retry()
        else:
            response = _call()

        # Extract text from Converse API response
        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        
        # Debug raw response structure if empty
        if not content_blocks or not message:
            print(f"[LLM DEBUG] Empty/unexpected response structure. Raw response keys: {response.keys()}", flush=True)
            print(f"[LLM DEBUG] output={output}, message={message}, content_blocks={content_blocks}", flush=True)
        
        text = content_blocks[0].get("text", "") if content_blocks else ""

        if text:
            usage = response.get("usage", {})
            print(
                f"[LLM] Bedrock Converse OK: model={target_model}, "
                f"input_tokens={usage.get('inputTokens', '?')}, "
                f"output_tokens={usage.get('outputTokens', '?')}, "
                f"response_len={len(text)}",
                flush=True,
            )
        else:
            usage = response.get("usage", {})
            print(
                f"[LLM DEBUG] Bedrock returned at least some tokens but text extraction failed! "
                f"model={target_model}, input_tokens={usage.get('inputTokens', '?')}, "
                f"output_tokens={usage.get('outputTokens', '?')}",
                flush=True,
            )
        return text

    except Exception as e:
        print(f"[LLM] Bedrock Converse failed (model={target_model}): {e}", flush=True)
        if os.getenv("DEBUG_LLM_ERRORS", "false").lower() in {"1", "true", "yes"}:
            traceback.print_exc()

        # Try fallback model if primary fails
        if target_model != BEDROCK_FALLBACK_MODEL and not model_id:
            print(f"[LLM] Trying fallback model: {BEDROCK_FALLBACK_MODEL}", flush=True)
            return _bedrock_converse(prompt, system, model_id=BEDROCK_FALLBACK_MODEL)

        return ""


def get_llm():
    """
    Returns a configured CrewAI LLM instance, or None if CrewAI is unavailable.
    Use direct_llm_call() when crewai is not installed.
    """
    if not CREWAI_AVAILABLE:
        return None

    try:
        from crewai import LLM

        # Priority 1: AWS Bedrock via CrewAI litellm integration
        if BEDROCK_AVAILABLE and _has_bedrock_credentials():
            try:
                return LLM(
                    model=f"bedrock/{BEDROCK_MODEL_ID}",
                    temperature=0.3,
                )
            except Exception as e:
                print(f"[LLM CONFIG] CrewAI Bedrock init failed, trying Anthropic: {e}", flush=True)

        # Priority 2: Direct Anthropic API key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if anthropic_key:
            return LLM(
                model="anthropic/claude-3-5-sonnet-20241022",
                api_key=anthropic_key,
                temperature=0.3,
            )
        elif openai_key:
            return LLM(
                model="gpt-4o-mini",
                api_key=openai_key,
                temperature=0.3,
            )
        return None
    except Exception:
        return None


def direct_llm_call(prompt: str, system: str = "") -> str:
    """
    Make a single LLM call without CrewAI.
    Priority: AWS Bedrock Converse → Anthropic SDK → OpenAI SDK → empty string.
    Returns the text response, or empty string on failure.
    """
    # ── Priority 1: AWS Bedrock (Converse API) ───────────────────────────────
    if BEDROCK_AVAILABLE and _has_bedrock_credentials():
        result = _bedrock_converse(prompt, system)
        if result:
            return result

    # ── Priority 2: Anthropic SDK ────────────────────────────────────────────
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if ANTHROPIC_AVAILABLE and anthropic_key:
        try:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=system or "You are a helpful financial advisor.",
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception:
            return ""

    # ── Priority 3: OpenAI SDK ───────────────────────────────────────────────
    if OPENAI_AVAILABLE and openai_key:
        try:
            import openai as _openai
            client = _openai.OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system or "You are a helpful financial advisor."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1024,
            )
            return resp.choices[0].message.content
        except Exception:
            return ""

    return ""


def is_live_mode() -> bool:
    """True if any LLM (Bedrock, CrewAI, or direct SDK) is available with credentials."""
    has_bedrock = BEDROCK_AVAILABLE and _has_bedrock_credentials()
    has_key = bool(os.getenv("ANTHROPIC_API_KEY")) or bool(os.getenv("OPENAI_API_KEY"))
    return has_bedrock or (has_key and (CREWAI_AVAILABLE or ANTHROPIC_AVAILABLE or OPENAI_AVAILABLE))


def is_crewai_mode() -> bool:
    """True if full multi-agent CrewAI orchestration is available."""
    has_bedrock = BEDROCK_AVAILABLE and _has_bedrock_credentials()
    has_key = bool(os.getenv("ANTHROPIC_API_KEY")) or bool(os.getenv("OPENAI_API_KEY"))
    return CREWAI_AVAILABLE and (has_bedrock or has_key)


def get_active_provider() -> str:
    """Returns a human-readable string indicating which LLM provider is active."""
    if BEDROCK_AVAILABLE and _has_bedrock_credentials():
        return f"AWS Bedrock ({BEDROCK_MODEL_ID}) [fallback: {BEDROCK_FALLBACK_MODEL}]"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "Anthropic Claude (direct API)"
    if os.getenv("OPENAI_API_KEY"):
        return "OpenAI (direct API)"
    return "Deterministic fallback (no LLM)"
