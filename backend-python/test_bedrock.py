#!/usr/bin/env python3
"""
AWS Bedrock LLM Model Test
Tests AWS credentials, Bedrock connectivity, and LLM inference.
"""

import os
import sys
from dotenv import load_dotenv

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

print("\n" + "=" * 70)
print("AWS BEDROCK LLM MODEL TEST")
print("=" * 70)

# ── Step 1: Check environment variables ──────────────────────────────────
print("\n[1/4] Checking AWS credentials from .env...")
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
session_token = os.getenv("AWS_SESSION_TOKEN")
region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
bedrock_model = os.getenv("BEDROCK_MODEL_ID", "deepseek.v3.2")

print(f"  ✓ AWS_DEFAULT_REGION: {region}")
print(f"  {'✓' if access_key else '✗'} AWS_ACCESS_KEY_ID: {access_key[:15]}..." if access_key else "  ✗ AWS_ACCESS_KEY_ID: NOT SET")
print(f"  {'✓' if secret_key else '✗'} AWS_SECRET_ACCESS_KEY: {secret_key[:15]}..." if secret_key else "  ✗ AWS_SECRET_ACCESS_KEY: NOT SET")
print(f"  {'✓' if session_token else '✗'} AWS_SESSION_TOKEN: {session_token[:15]}..." if session_token else "  ✗ AWS_SESSION_TOKEN: NOT SET")
print(f"  ✓ BEDROCK_MODEL_ID: {bedrock_model}")

if not (access_key and secret_key):
    print("\n✗ Missing AWS credentials. Cannot proceed.")
    sys.exit(1)

# ── Step 2: Test boto3 import and client creation ─────────────────────────
print("\n[2/4] Testing boto3 and AWS client...", end=" ")
try:
    import boto3
    print("✓")
except ImportError:
    print("✗ boto3 not installed")
    print("  Run: pip install boto3")
    sys.exit(1)

try:
    session = boto3.Session(
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
    )
    client = session.client("bedrock-runtime")
    print("      ✓ Boto3 session and bedrock-runtime client created")
except Exception as e:
    print(f"      ✗ Failed to create client: {e}")
    sys.exit(1)

# ── Step 3: List available Bedrock models ────────────────────────────────
print("\n[3/4] Checking Bedrock model availability...")
models_to_test = [bedrock_model, "qwen.qwen3-235b-a22b-2507-v1:0"]
available_models = []

for model_id in models_to_test:
    try:
        response = client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "test"}]}],
            inferenceConfig={"maxTokens": 10, "temperature": 0.3}
        )
        print(f"  ✓ {model_id}: Available")
        available_models.append(model_id)
    except Exception as e:
        error_msg = str(e)
        if "AccessDeniedException" in error_msg or "not accessible" in error_msg:
            print(f"  ✗ {model_id}: Access denied (model may need approval)")
        elif "ValidationException" in error_msg:
            print(f"  ✗ {model_id}: Not available in region {region}")
        else:
            print(f"  ✗ {model_id}: {error_msg[:50]}")

if not available_models:
    print("\n✗ No Bedrock models available. Check region and model access.")
    sys.exit(1)

# ── Step 4: Test actual LLM inference ────────────────────────────────────
print("\n[4/4] Testing LLM inference...")
test_model = available_models[0]
test_prompt = "What is the capital of France? Answer in one word."

try:
    print(f"  Testing model: {test_model}")
    print(f"  Prompt: \"{test_prompt}\"")
    print(f"  Calling Bedrock Converse API...", end=" ")
    
    response = client.converse(
        modelId=test_model,
        system=[{"text": "You are a helpful assistant. Answer concisely."}],
        messages=[
            {
                "role": "user",
                "content": [{"text": test_prompt}],
            }
        ],
        inferenceConfig={
            "maxTokens": 256,
            "temperature": 0.3,
        },
    )
    
    output = response.get("output", {})
    message = output.get("message", {})
    content_blocks = message.get("content", [])
    response_text = content_blocks[0].get("text", "") if content_blocks else ""
    
    if response_text:
        usage = response.get("usage", {})
        print("✓")
        print(f"\n  Response: {response_text}")
        print(f"  Input tokens: {usage.get('inputTokens', '?')}")
        print(f"  Output tokens: {usage.get('outputTokens', '?')}")
        print(f"  Stop reason: {response.get('stopReason', '?')}")
    else:
        print("✗ Empty response from model")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

# ── Success ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED - AWS Bedrock LLM is working!")
print("=" * 70)
print(f"\nYour backend can use:")
print(f"  • Model: {test_model}")
print(f"  • Region: {region}")
print(f"  • LLM mode: Full inference via Bedrock Converse API")
print("\n")
