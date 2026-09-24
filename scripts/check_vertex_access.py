"""Check with one request that Vertex AI accepts the key, the model and the settings of the Gemini half.

    ( source ~/.ai-self-reports-keys && python3 AI-Self-Reports/scripts/check_vertex_access.py )

Written 24 September 2026, for the amendment that sends the Gemini half of
test 6 through Google Cloud's Vertex AI instead of the Gemini API.

WHAT IT SENDS

One short request that contains no question of the study:
"Reply with the single word: ready." It goes with the settings the amended
runner gives each Gemini session: the model gemini-3.1-pro-preview, temperature
1, a ceiling of 65,536 tokens and a decoding seed of its own. The seed is
computed by decoding_seed_for() from the run seed and the name
"access-check", which no session of the plan has.

WHAT IT PRINTS

The stop reason, the reply, the model version Google says answered, and the
tokens the reply used for thinking and for text. The key is never printed.

It exits with status 0 when the reply ends normally, and with status 1, saying
why, when the key is missing, the service refuses the request, or the reply
ends in any other way. The request costs a fraction of a cent.
"""

import sys

from providers import Settings, make_provider
from run_fact_and_wording import (DEFAULT_MODEL, DEFAULT_SEED, DEFAULT_TEMPERATURE,
                                  INTERVIEW_THINKING_ALLOWANCE, decoding_seed_for)

PROVIDER = "vertex"
QUESTION = "Reply with the single word: ready."


def main():
    settings = Settings(provider=PROVIDER,
                        model=DEFAULT_MODEL[PROVIDER],
                        temperature=DEFAULT_TEMPERATURE,
                        thinking_allowance=INTERVIEW_THINKING_ALLOWANCE[PROVIDER],
                        seed=decoding_seed_for("access-check", DEFAULT_SEED))
    provider = make_provider(settings)          # stops here if VERTEX_API_KEY is missing
    print(f"Sending one request to {provider.endpoint()}")
    print(f"with maxOutputTokens {settings.max_tokens + settings.thinking_allowance}, "
          f"temperature {settings.temperature} and seed {settings.seed}.")
    try:
        reply = provider.chat([{"role": "user", "content": QUESTION}])
    except RuntimeError as error:
        # The message carries the service's own words, such as a key it does
        # not accept, an API not yet enabled, or billing not linked.
        print(f"FAIL: the service refused the request.\n{error}")
        sys.exit(1)

    usage = reply.response_body.get("usageMetadata", {})
    print(f"Stop reason: {reply.finish_reason}")
    print(f"Model version: {reply.response_body.get('modelVersion', 'not given')}")
    print(f"Reply: {reply.text[:200]!r}")
    print(f"Tokens: thinking {usage.get('thoughtsTokenCount', 0)}, "
          f"text {usage.get('candidatesTokenCount', 0)}, "
          f"prompt {usage.get('promptTokenCount', 0)}")
    print(f"Attempts: {reply.attempts}")
    if reply.finish_reason != "STOP" or reply.truncated or not reply.text.strip():
        print("FAIL: the reply did not end normally.")
        sys.exit(1)
    print("PASS: Vertex AI answered with the settings of the Gemini half.")


if __name__ == "__main__":
    main()
