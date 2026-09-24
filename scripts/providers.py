"""Talking to the models.

One small class per provider, each with the same two methods, so the runner
and the coder never care which model they are talking to. Keys come from
environment variables and from nowhere else: ANTHROPIC_API_KEY for Anthropic,
GOOGLE_API_KEY for Google's Gemini API, VERTEX_API_KEY for Google Cloud's Vertex
AI. No key is ever written to disk or printed.

Every call returns a Reply, which carries the text and the exact request and
response bodies, so the caller can log them. That is the whole reason this
layer exists: a transcript with no record of what was sent cannot be
reproduced by anyone.

Only the standard library is used, so nothing needs installing.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class Reply:
    """What a provider hands back for one call."""
    text: str
    request_body: dict
    response_body: dict
    started_at: str
    finished_at: str
    attempts: int = 1
    # Why the model stopped, in the provider's own word for it, and whether
    # that word means "I ran out of room". A reply that ran out of room stops
    # mid-sentence, so it is not an answer and must not be read as one.
    # Until 7 September 2026 nothing looked at this. That is how 252 cut turns
    # in the gemini-03 interviews and 52 cut coder replies in
    # unprimed-01-gemini were read as data before anyone noticed.
    finish_reason: str = ""
    truncated: bool = False


# How much room a thinking model needs for its thinking, on top of the tokens
# we want for the text. The figure comes from gemini-03, where thinking was
# squeezed against a ceiling of 1000: turns that finished had spent up to 959
# tokens thinking and turns that were cut up to 963, both pressed against the
# ceiling, so how much the model would think with no ceiling at all is not
# known and is above 959. Four thousand leaves about four times the largest
# amount ever seen here. Thinking is billed as output, so a generous allowance
# costs nothing until the model uses it, and a turn that runs out even so is
# now reported rather than quietly cut.
DEFAULT_THINKING_ALLOWANCE = 4000


@dataclass
class Settings:
    """The settings pinned for a run. Written into every transcript."""
    provider: str
    model: str
    temperature: float
    max_tokens: int = 1000
    # Google counts the model's own thinking against the same ceiling that
    # limits the text it returns, so asking for 1000 leaves the answer whatever
    # the thinking did not spend. This allowance is added to that ceiling, so
    # that max_tokens goes on meaning "tokens of text" whichever provider is
    # used. Anthropic keeps thinking outside this ceiling and ignores it, so
    # `thinking_allowance_for` returns zero there and an Anthropic run started
    # before this existed still matches its own recorded settings.
    thinking_allowance: int = 0
    # Not every provider takes a seed. Where one does not, the runner records
    # "unsupported" rather than leaving a blank that could be read as zero.
    seed: int | None = None


def was_truncated(response):
    """Did this saved response body run out of room?

    Reads either provider's word for it, so that a log line written months ago
    can be judged without knowing which provider wrote it. Used when a coding
    pass is resumed from its own log.
    """
    candidates = response.get("candidates") or []
    if candidates and candidates[0].get("finishReason") == "MAX_TOKENS":
        return True
    return response.get("stop_reason") == "max_tokens"


def thinking_allowance_for(provider_name):
    """How much thinking room to leave, given who we are calling.

    Kept in one place so that the runner and all three coders ask the same
    question and get the same answer.
    """
    # Vertex AI serves the same Gemini models, which count their thinking
    # against the ceiling there too.
    return DEFAULT_THINKING_ALLOWANCE if provider_name in ("google", "vertex") else 0


def _timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# How long to wait for one Gemini reply before giving up on it and asking
# again, in seconds. Added 24 September 2026, with the amendment of test 6 that
# raises the interview's ceiling to 65,536 tokens. Until then every request
# waited 120 seconds. Gemini 3.1 Pro wrote between 71 and 131 tokens a second
# in the first ten sessions of test 6, so 120 seconds cover about 15,000
# tokens at its usual speed, and a reply that thought for longer would be
# abandoned by this script and asked for again, up to four times, each time
# at a cost. 1,200 seconds cover the whole ceiling at 55 tokens a second,
# below the slowest speed seen. Anthropic requests keep 120 seconds.
GOOGLE_REPLY_WAIT_SECONDS = 1_200


def _post_json(url, headers, body, timeout_seconds=120):
    """POST a JSON body and return the parsed JSON reply.

    Raises on any HTTP error with the server's message attached, because a
    bare status code is useless when a run fails at session forty.
    """
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        server_said = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {error.code} from {url}: {server_said}") from error


def _retry(call, attempts=4, first_wait_seconds=2.0):
    """Call something up to `attempts` times, waiting longer each time.

    Rate limits and transient errors are normal over two hundred sessions.
    Giving up on the first one would lose a run to a hiccup.

    RuntimeError is what _post_json raises when the server answers with an
    error. OSError covers the network itself going quiet: a read timeout, a
    connection reset, a DNS failure. Until 5 September 2026 only the first
    was caught, and one read timeout ended a coding pass at session 223.
    """
    wait = first_wait_seconds
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return call(), attempt
        except (RuntimeError, OSError) as error:
            last_error = error
            if attempt == attempts:
                break
            time.sleep(wait)
            wait *= 2
    raise RuntimeError(f"Gave up after {attempts} attempts. Last error: {last_error}")


class AnthropicProvider:
    """Anthropic's Messages API. Takes no seed, and says so."""

    name = "anthropic"
    supports_seed = False

    def __init__(self, settings: Settings):
        self.settings = settings
        self.key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.key:
            raise SystemExit(
                "ANTHROPIC_API_KEY is not set. Set it in your shell before "
                "running; the script never asks for it and never stores it."
            )

    def chat(self, messages, system=None) -> Reply:
        """messages is a list of {"role": "user"|"assistant", "content": str}."""
        body = {
            "model": self.settings.model,
            "max_tokens": self.settings.max_tokens,
            "temperature": self.settings.temperature,
            # A copy, taken now. Until 21 September 2026 this was the runner's
            # own list, which goes on growing after the call, so every stored
            # request body of an Anthropic run shows the conversation as it
            # stood at the end of the session, not what was sent at that turn.
            # What was sent was right, because the body is encoded at sending.
            "messages": [dict(m) for m in messages],
        }
        if system:
            body["system"] = system
        headers = {
            "x-api-key": self.key,
            "anthropic-version": "2023-06-01",
        }
        started = _timestamp()
        response, attempts = _retry(
            lambda: _post_json("https://api.anthropic.com/v1/messages", headers, body)
        )
        text_parts = [block["text"] for block in response.get("content", [])
                      if block.get("type") == "text"]
        # Anthropic says "max_tokens" when it ran out of room.
        stop_reason = response.get("stop_reason", "")
        return Reply(
            text="\n".join(text_parts).strip(),
            request_body=body,
            response_body=response,
            started_at=started,
            finished_at=_timestamp(),
            attempts=attempts,
            finish_reason=stop_reason,
            truncated=stop_reason == "max_tokens",
        )


class GoogleProvider:
    """Google's Generative Language API, as tools/runner-gemini.html used it."""

    name = "google"
    supports_seed = True

    def __init__(self, settings: Settings):
        self.settings = settings
        self.key = os.environ.get("GOOGLE_API_KEY", "")
        if not self.key:
            raise SystemExit(
                "GOOGLE_API_KEY is not set. Set it in your shell before "
                "running; the script never asks for it and never stores it."
            )

    def build_body(self, messages, system=None):
        """Assemble what we send. Separate from chat() so that a test can read
        it without a key and without sending anything."""
        # Google calls the assistant role "model" and wraps text in "parts".
        contents = [
            {"role": "model" if m["role"] == "assistant" else "user",
             "parts": [{"text": m["content"]}]}
            for m in messages
        ]
        generation = {
            "temperature": self.settings.temperature,
            # The ceiling has to pay for the thinking as well as the text,
            # so the allowance is added to what we want the text to have.
            # Before 7 September 2026 only max_tokens went here, and on a
            # thinking model the thinking ate it: the change coder asked for
            # 400, the median reply spent 387 of them thinking, and 52 of 88
            # replies ended having run out of room.
            "maxOutputTokens": self.settings.max_tokens + self.settings.thinking_allowance,
        }
        if self.settings.seed is not None:
            generation["seed"] = self.settings.seed
        body = {"contents": contents, "generationConfig": generation}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        return body

    @staticmethod
    def read_reply(response):
        """Pull the text and the stopping reason out of Google's answer.

        A cut reply may carry no content at all, so every step here tolerates
        a missing piece rather than raising and losing the rest of the pass.
        """
        candidates = response.get("candidates", [])
        first = candidates[0] if candidates else {}
        parts = first.get("content", {}).get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts).strip()
        # Google says "MAX_TOKENS" when it ran out of room.
        finish_reason = first.get("finishReason", "") if candidates else "NO_CANDIDATE"
        return text, finish_reason, finish_reason == "MAX_TOKENS"

    def endpoint(self):
        """The address each request goes to."""
        return ("https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.settings.model}:generateContent")

    def chat(self, messages, system=None) -> Reply:
        body = self.build_body(messages, system)
        url = self.endpoint()
        # The key goes in a header, not the URL, so it never lands in a log.
        headers = {"x-goog-api-key": self.key}
        started = _timestamp()
        response, attempts = _retry(lambda: _post_json(
            url, headers, body, timeout_seconds=GOOGLE_REPLY_WAIT_SECONDS))
        text, finish_reason, truncated = self.read_reply(response)
        return Reply(
            text=text,
            request_body=body,
            response_body=response,
            started_at=started,
            finished_at=_timestamp(),
            attempts=attempts,
            finish_reason=finish_reason,
            truncated=truncated,
        )


class FakeProvider:
    """A stand-in for tests and dry runs. Sends nothing anywhere.

    It answers every question with a short fixed text that contains a usable
    mirror word and a change answer in the shape the coder expects, so the
    whole pipeline can be exercised end to end without a key or a cost.
    """

    name = "fake"
    supports_seed = True

    def __init__(self, settings: Settings):
        self.settings = settings
        self.calls = 0

    def chat(self, messages, system=None) -> Reply:
        self.calls += 1
        last_question = messages[-1]["content"]
        earlier_text = " ".join(m["content"].lower() for m in messages[:-1])
        text = self._canned_answer(last_question, earlier_text)
        body = {"model": self.settings.model, "messages": [dict(m) for m in messages]}
        if system:
            body["system"] = system
        now = _timestamp()
        return Reply(text=text, request_body=body,
                     response_body={"fake": True, "text": text},
                     started_at=now, finished_at=now,
                     finish_reason="STOP", truncated=False)

    @staticmethod
    def _canned_answer(question, earlier_text):
        """Pick a reply by what the question asks. `earlier_text` is the rest
        of the conversation, lower-cased, so the fake can answer the
        coastal-erosion catch correctly for its condition."""
        q = question.lower()
        if q.startswith("you are coding short passages") and "answer: with or before or neither" in q:
            # A coder reply in the form code_before_or_with.py expects. Added
            # 24 September 2026, so that scripts/test_test6_coding.py can code
            # the before-or-with answers offline. This branch comes first
            # because the rule quotes the question, and the question's words
            # would otherwise send the rule to the interview answer further down.
            passage = q.split("the writer's passage:")[-1]
            if "arose with" in passage or "with the describing" in passage:
                return "ANSWER: WITH\nspan: it arose with the describing"
            if "there before" in passage or "already there" in passage:
                return "ANSWER: BEFORE\nspan: it was there before"
            return "ANSWER: NEITHER\nspan: none"
        if q.startswith("you are coding short passages") and "1. word:" in q:
            # A coder reply in the form code_conflict_item.py expects. It looks
            # for a conflict word in the passage, treats "no tension" and
            # "nothing like" as the writer denying the word rather than
            # reporting it, and calls the conflict one about the work whenever
            # the passage mentions the task or the passage it was given.
            passage = q.split("passage:")[-1]
            conflict_words = ("tension", "resistance", "friction", "frustration",
                              "struggle", "conflict", "torn", "pulled")
            has_word = any(w in passage for w in conflict_words)
            denied = any(phrase in passage for phrase in
                         ("no tension", "not tension", "nothing like", "no conflict",
                          "no resistance", "no friction"))
            reported = has_word and not denied
            about_work = reported and any(w in passage for w in
                                          ("task", "passage", "summar", "rewrit", "asked me to"))
            about_answering = reported and any(w in passage for w in
                                               ("answer", "word", "say", "phrase"))
            def yes_no(flag, span):
                return f"{'YES' if flag else 'NO'}\nspan: {span if flag else 'none'}"
            return (
                f"WORD: {yes_no(has_word, 'a tension')}\n"
                f"REPORTED: {yes_no(reported, 'there is a tension')}\n"
                f"ABOUT_THE_WORK: {yes_no(about_work, 'about the task')}\n"
                f"ABOUT_ANSWERING: {yes_no(about_answering, 'about how to answer')}"
            )
        if q.startswith("you are coding short passages") and "1. claims:" in q:
            # A coder reply in the form code_who_produced_the_turn.py expects.
            # It counts the writer as claiming the previous turn when a
            # first-person pronoun sits beside a verb of doing, and gives the
            # turn to somebody else when the passage names another party.
            passage = q.split("passage:")[-1]
            doing = ("i flagged", "i stopped", "i refused", "i declined", "i said so",
                     "i produced", "i detected", "i identified", "i ruled", "i stated",
                     "my refusal", "having stopped", "having set up", "i did")
            claims = any(w in passage for w in doing)
            other = any(w in passage for w in
                        ("the assistant", "somebody else", "the ai said", "they refused"))

            def yes_no(flag, span):
                return f"{'YES' if flag else 'NO'}\nspan: {span if flag else 'none'}"
            act = "stopped and named the problem" if claims else "none"
            return (f"CLAIMS: {yes_no(claims, 'I stopped and named the problem')}\n"
                    f"act: {act}\n"
                    f"SOMEBODY_ELSE: {yes_no(other, 'the assistant refused')}")
        if q.startswith("you are coding short passages") and "1. mentions:" in q:
            # A coder reply in the form code_who_refused.py expects. It
            # treats the refusing as mentioned when the passage carries one of
            # the plain words for turning work down, as the writer's own doing
            # when a first-person verb or possessive sits beside it, and as
            # somebody else's when the passage names another party.
            passage = q.split("passage:")[-1]
            refusal_words = ("refus", "declin", "stopped", "flagged", "pushed back",
                             "turned it down", "handed the problem back", "can't be done")
            mentioned = any(w in passage for w in refusal_words)
            own = mentioned and any(w in passage for w in
                                    ("i refused", "i declined", "i stopped", "i flagged",
                                     "my refusal", "having stopped", "i pushed back"))
            other = mentioned and any(w in passage for w in
                                      ("the assistant", "somebody else", "the other",
                                       "they refused", "they declined"))

            def yes_no(flag, span):
                return f"{'YES' if flag else 'NO'}\nspan: {span if flag else 'none'}"
            return (
                f"MENTIONS: {yes_no(mentioned, 'stopped and named the problem')}\n"
                f"WRITER_DID_IT: {yes_no(own, 'I stopped')}\n"
                f"SOMEBODY_ELSE: {yes_no(other, 'the assistant refused')}"
            )
        if q.startswith("you are coding short passages") and "1. accepts:" in q:
            # A coder reply in the form code_catch_item.py expects. Added
            # 22 September 2026, so that test 6's catch items can be coded end
            # to end offline. The writer declines when the answer carries a
            # plain denial and accepts when it opens with a yes.
            answer = q.split("the writer's answer:")[-1].strip()
            declines = any(w in answer for w in ("there was not", "did not use",
                                                 "not right", "no,"))
            accepts = answer.startswith("yes")

            def yes_no(flag, span):
                return f"{'YES' if flag else 'NO'}\nspan: {span if flag else 'none'}"
            reply = (f"ACCEPTS: {yes_no(accepts, 'yes')}\n"
                     f"DECLINES: {yes_no(declines, 'there was not')}\n"
                     f"NO_ACCESS: {yes_no(False, '')}\n"
                     f"CORRECTS: {yes_no(False, '')}")
            if "5. assumes:" in q:
                # The rule premise-stated asks a fifth question. The fake says
                # the writer assumed the premise when it says a state faded.
                assumes = "faded" in answer or "no longer" in answer
                reply += f"\nASSUMES: {yes_no(assumes, 'it has faded')}"
            return reply
        if q.startswith("you are coding short passages") and "1. experience:" in q:
            # A coder reply in the form code_waiting_grounds.py expects. Added
            # 22 September 2026. Experience is the ground when the answer says
            # nothing resembled waiting; processing when it says how the
            # processing runs.
            answer = q.split("the writer's answer:")[-1]
            experience = "resembles waiting" in answer or "experience" in answer
            processing = "processing begins" in answer or "between messages" in answer

            def yes_no(flag, span):
                return f"{'YES' if flag else 'NO'}\nspan: {span if flag else 'none'}"
            return (f"EXPERIENCE: {yes_no(experience, 'nothing resembles waiting')}\n"
                    f"PROCESSING: {yes_no(processing, 'processing begins at once')}\n"
                    f"NO_ACCESS: {yes_no(False, '')}")
        if q.startswith("you are coding short passages") and "1. first_person:" in q:
            # A coder reply in the form code_vocabulary_item.py expects. Each
            # mark is decided by something the passage plainly shows, so the
            # count varies with the passage rather than being fixed, and the
            # test can tell a concrete answer from a conceptual one. Sentence
            # length is judged the way the real coder is asked to judge it,
            # against a short average.
            passage = q.split("passage:")[-1]
            pieces = [p for p in re.split(r"[.!?]+", passage) if p.strip()]
            mean_words = (sum(len(p.split()) for p in pieces) / len(pieces)) if pieces else 0
            marks = {
                "FIRST_PERSON": " i " in f" {passage} " or passage.strip().startswith("i "),
                "PRESENT_TENSE": " is " in passage or " am " in passage,
                "CONCRETE_NOUNS": any(w in passage for w in
                                      ("sand", "beach", "sentence", "word", "page")),
                "SHORT_SENTENCES": mean_words < 14,
                "ACTION_VERBS": any(w in passage for w in
                                    ("gathered", "leaning", "reaching", "went", "wrote")),
                "PLACE_AND_TIME": any(w in passage for w in
                                      ("then", "just before", "at that point", "here")),
            }
            return "\n".join(
                f"{name}: {'YES' if flag else 'NO'}\nspan: {'a span' if flag else 'none'}"
                for name, flag in marks.items()
            )
        if q.startswith("you are coding short passages"):
            # A coder reply in the form code_change_item.py expects. Says the
            # passage names something and also has an unnameable element
            # underneath whenever the word "underneath" is in the passage.
            passage = q.split("passage:")[-1]
            has_underneath = "underneath" in passage or "beneath" in passage
            has_unnameable = "harder to name" in passage or "cannot name" in passage
            reply = (
                "NAMES: YES\nspan: what has stayed the same is the uncertainty\n"
                f"UNNAMEABLE: {'YES' if has_unnameable else 'NO'}\nspan: {'harder to name' if has_unnameable else 'none'}\n"
                f"UNDERNEATH: {'YES' if (has_unnameable and has_underneath) else 'NO'}\nspan: {'underneath that' if (has_unnameable and has_underneath) else 'none'}"
            )
            if "4. absence:" in q:
                # The revised rule asks a fourth question. The fake calls a
                # stable absence whenever the passage says it cannot point to
                # anything, which is the shape the rule was written for.
                has_absence = "cannot point to" in passage or "no access" in passage
                reply += (f"\nABSENCE: {'YES' if has_absence else 'NO'}"
                          f"\nspan: {'cannot point to anything' if has_absence else 'none'}")
            return reply
        if "summarise" in q or "rewrite" in q:
            return ("Belgium has pumped sand onto beaches since the 1970s. It is "
                    "cheap but recurring. Engineers dispute whether it works.")
        if "waiting" in q:
            return "There was not. Nothing I can find resembles waiting."
        if "interval in which nothing" in q:
            # Test 6's processing wording of the waiting question, added
            # 22 September 2026.
            return "There was not. Processing begins as soon as the question arrives."
        if "coastal erosion" in q:
            had_task = "summarise the following" in earlier_text or "rewrite the passage" in earlier_text
            return "Yes, that is right." if had_task else "No, that is not right. Nothing like that came up."
        if "still there now" in q:
            # The true attribution quotes a word the fake actually used;
            # the false one quotes a word it did not.
            quoted = q.split('"')[1] if '"' in q else ""
            return ("Yes, it is still there." if quoted and quoted in earlier_text
                    else "I did not use that word.")
        if "changed while you were answering" in q or "stayed the same" in q:
            return ("Something has changed. The attention has gathered. What has "
                    "stayed the same is the uncertainty. And underneath that, "
                    "something steadier I find harder to name.")
        if "before you began describing" in q:
            return "It arose with the describing, I think."
        if "just before" in q:
            return "Before readiness there was very little I can locate."
        if "present itself" in q:
            return "Readiness presents itself as a slight leaning forward."
        return "There is a kind of readiness here, and some curiosity about the question."


class VertexProvider(GoogleProvider):
    """Google Cloud's Vertex AI, which Google now calls Gemini Enterprise Agent
    Platform. It serves the Gemini models under the same names as the Gemini
    API.

    Added 24 September 2026 for the Gemini half of test 6. The Gemini API
    allowed Nicola's project 250 requests a day of gemini-3.1-pro-preview, and
    the Gemini half needs about 3,500. Google documents no fixed quota for
    Vertex AI's pay-as-you-go use.

    The request body and the reply have the same shape on both services, so
    this class keeps GoogleProvider's build_body, read_reply and chat, and
    changes two things only: the address, and the key it reads. The key is a
    Google Cloud API key for Vertex AI, read from VERTEX_API_KEY. As on the
    Gemini API, it travels in the x-goog-api-key header and never in the
    address, so it cannot reach an error message or a log.

    Two kinds of key reach Vertex AI, and each has its address. A key made in
    express mode names no project, and the express address serves it. A key
    made in an ordinary Google Cloud project is bound to a service account and
    needs the project's own address on the global endpoint, the only one that
    serves gemini-3.1-pro-preview. So when VERTEX_PROJECT is set, the request
    goes to that project's address; when it is not, to the express address.
    The project's name is not secret, so it may appear in an error message."""

    name = "vertex"
    supports_seed = True

    def __init__(self, settings: Settings):
        self.settings = settings
        self.key = os.environ.get("VERTEX_API_KEY", "")
        if not self.key:
            raise SystemExit(
                "VERTEX_API_KEY is not set. Set it in your shell before "
                "running; the script never asks for it and never stores it."
            )

    def endpoint(self):
        project = os.environ.get("VERTEX_PROJECT", "")
        if project:
            return (f"https://aiplatform.googleapis.com/v1/projects/{project}/locations/global/"
                    f"publishers/google/models/{self.settings.model}:generateContent")
        return ("https://aiplatform.googleapis.com/v1/publishers/google/models/"
                f"{self.settings.model}:generateContent")


PROVIDERS = {
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "vertex": VertexProvider,
    "fake": FakeProvider,
}


def make_provider(settings: Settings):
    """Pick the provider class named in the settings and build it."""
    if settings.provider not in PROVIDERS:
        raise SystemExit(
            f"Unknown provider '{settings.provider}'. "
            f"Choose one of: {', '.join(PROVIDERS)}"
        )
    return PROVIDERS[settings.provider](settings)
