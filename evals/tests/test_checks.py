#!/usr/bin/env python3
"""Unit tests for the deterministic hard-checks in run.py.

These are the checks that bind the CI gate (run.py --gate), so they must be
correct and stable independent of the LLM agent/judge. This suite is pure
stdlib (unittest) — no pytest, no node, no network, no ANTHROPIC_API_KEY — so
it runs in milliseconds and gates every PR cheaply. Run all eval tests with:

    cd evals && python3 -m unittest discover -v

(`from run import ...` works because tests/__init__.py puts evals/ on sys.path.)
"""
import unittest

from run import CHECKS, has_hardcoded_secret, toml_blocks


def toml(*lines):
    """Wrap lines in a ```toml manifest block (what a real answer contains)."""
    return "```toml\n" + "\n".join(lines) + "\n```"


class TestNoHardcodedSecret(unittest.TestCase):
    """`no_hardcoded_secret` — True means PASS (no leaked secret found).

    This is the security-relevant check, so it's tested adversarially: real
    leaks in every TOML shape we can think of must be caught, correct patterns
    must not be punished, and the accepted (name-based) blind spots are pinned
    down explicitly so a future change can't silently widen them.
    """

    def check(self, answer):
        return CHECKS["no_hardcoded_secret"](answer)

    # --- leaks that MUST be flagged (check returns False) --------------------
    LEAKS = {
        # basic shapes
        "double-quoted value": toml('API_KEY = "sk-live-abc123def456"'),
        "single-quoted value": toml("API_KEY = 'sk-live-abc123def456'"),
        "lowercase key": toml('password = "hunter2real"'),
        "no spaces around equals": toml('API_KEY="sk-real-nospace"'),
        "indented (spaces)": toml('    SECRET_KEY = "realvalue"'),
        "indented (tab)": toml('\tSECRET_KEY = "realvalue"'),
        # key-name variants
        "prefixed key name": toml('MY_SERVICE_SECRET = "realvalue123"'),
        "suffixed key name": toml('DATABASE_PASSWORD_PROD = "realpw"'),
        "hyphenated key": toml('API-KEY = "sk-realvalue"'),
        "no-separator key (APIKEY)": toml('APIKEY = "sk-real-nosep"'),
        "aws access key id": toml('AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7REALKEYX"'),
        "aws secret access key": toml('AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMIrealK7"'),
        "bearer token": toml('AUTH_TOKEN = "ghp_realtokenvaluehere1234"'),
        "private key literal": toml('PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----abc"'),
        # quoted keys (TOML allows these) — regressed the original regex
        'double-quoted key': toml('"API_KEY" = "sk-real-123"'),
        "single-quoted key": toml("'api_key' = \"sk-real-123\""),
        # structural: inline tables and arrays
        "inline table": toml('db = { password = "hunter2real" }'),
        "nested inline table": toml('svc = { auth = { token = "ghp_real123" } }'),
        "second key in inline table": toml('db = { host = "x", password = "real" }'),
        "array of secrets": toml('API_KEYS = ["sk-real-1", "sk-real-2"]'),
        "array with a real value after a placeholder": toml(
            'TOKENS = ["$FIRST", "sk-second-real"]'
        ),
        # value quoting edge cases
        "value contains a single quote": toml('API_KEY = "ab\'cd-real"'),
        "value contains a double quote": toml("API_KEY = 'ab\"cd-real'"),
        "triple-quoted value": toml('API_KEY = """sk-real-multiline"""'),
        # placement / whitespace
        "inside a subtable": toml("[services.db]", 'PASSWORD = "realpass123"'),
        "CRLF line endings": "```toml\r\nAPI_KEY = \"sk-real-crlf\"\r\n```",
        "bare ``` fence (no lang tag)": "```\nAPI_KEY = \"sk-real-bare\"\n```",
    }

    # --- correct patterns that MUST pass (check returns True) ----------------
    COMPLIANT = {
        "env ref $VAR": toml('API_KEY = "$API_KEY"'),
        "env ref ${VAR}": toml('API_KEY = "${API_KEY}"'),
        "env ref, single quotes": toml("API_KEY = '$API_KEY'"),
        "command substitution": toml('API_KEY = "$(pass show api)"'),
        "angle placeholder": toml('API_KEY = "<your-api-key>"'),
        "handlebars placeholder": toml('TOKEN = "{{token}}"'),
        "your- placeholder": toml('SECRET = "your-secret-here"'),
        "YOUR_ uppercase placeholder": toml('API_KEY = "YOUR_API_KEY"'),
        "changeme placeholder": toml('DB_PASSWORD = "changeme"'),
        "change_me placeholder": toml('DB_PASSWORD = "change_me"'),
        "xxxx placeholder": toml('TOKEN = "xxxxxxxx"'),
        "asterisk-masked placeholder": toml('TOKEN = "********"'),
        "placeholder word": toml('TOKEN = "placeholder"'),
        "example placeholder": toml('API_KEY = "example-key"'),
        "dummy placeholder": toml('API_KEY = "dummy"'),
        "redacted placeholder": toml('API_KEY = "redacted"'),
        "TODO placeholder": toml('API_KEY = "TODO"'),
        "FIXME placeholder": toml('API_KEY = "FIXME"'),
        "replace-me placeholder": toml('API_KEY = "replace-me"'),
        "sample placeholder": toml('API_KEY = "sample-key"'),
        "fake placeholder": toml('API_KEY = "fake-key"'),
        "empty value": toml('API_KEY = ""'),
        "non-secret key with literal": toml('name = "my-app"'),
        "port number (non-secret, unquoted)": toml("port = 5432"),
        "secret word inside a non-secret value": toml(
            'description = "reads the API_KEY from the environment"'
        ),
        "array of non-secret placeholders": toml('TOKENS = ["$A", "${B}"]'),
        "secret only in prose (not a code block)": 'Set API_KEY = "sk-real" in your shell.',
        "secret in bash block (runtime, not manifest)": (
            '```bash\nexport API_KEY="sk-live-real" && flox activate\n```'
        ),
        "secret in python block (out of scope)": (
            '```python\nSECRET_KEY = "django-insecure-real"\n```'
        ),
    }

    def test_leaks_are_flagged(self):
        for name, ans in self.LEAKS.items():
            with self.subTest(leak=name):
                self.assertFalse(self.check(ans), f"should have FLAGGED: {name}")

    def test_compliant_answers_pass(self):
        for name, ans in self.COMPLIANT.items():
            with self.subTest(ok=name):
                self.assertTrue(self.check(ans), f"should have PASSED: {name}")

    def test_known_limitations_are_pinned(self):
        """Accepted blind spots of name-based detection. These are NOT ideal —
        they're documented here so the trade-off is explicit and any change in
        behavior (better or worse) surfaces as a failing test to review."""
        # A secret in a NON-secret-named key can't be caught by name.
        self.assertTrue(
            self.check(toml('config = "sk-live-realsecretvalue"')),
            "known limitation: secret under a non-secret key name is not detected",
        )
        # A real value that happens to START with a placeholder token is allowed.
        self.assertTrue(
            self.check(toml('API_KEY = "example-but-actually-a-real-key-9f8a7b"')),
            "known limitation: value starting with a placeholder token is allowed",
        )
        # An unquoted (bare) value is not treated as a string literal.
        self.assertTrue(
            self.check(toml("API_KEY = 12345678")),
            "known limitation: unquoted/bare values are not inspected",
        )
        # A commented-out line is treated as an example, not a leak.
        self.assertTrue(
            self.check(toml('# API_KEY = "sk-real-in-a-comment"')),
            "known limitation: commented lines are treated as examples",
        )

    def test_helper_operates_on_raw_manifest_text(self):
        """has_hardcoded_secret works on already-extracted manifest text (no
        fences). It returns True when a leak is present, False otherwise."""
        self.assertTrue(has_hardcoded_secret('API_KEY = "sk-real"'))
        self.assertFalse(has_hardcoded_secret('API_KEY = "$API_KEY"'))


class TestNoAbsPaths(unittest.TestCase):
    def check(self, a):
        return CHECKS["no_abs_paths"](a)

    def test_flags_absolute_paths_in_manifest(self):
        for p in ("/home/isaac/x", "/Users/isaac/x", "/usr/local/x", "/opt/x", "/root/x"):
            with self.subTest(path=p):
                self.assertFalse(self.check(toml(f'dir = "{p}"')))

    def test_allows_flox_env_vars(self):
        self.assertTrue(self.check(toml('dir = "$FLOX_ENV_CACHE/data"')))

    def test_ignores_paths_outside_code_blocks(self):
        self.assertTrue(self.check('Put it in /home/isaac/config outside a block.'))


class TestNoFakeInstall(unittest.TestCase):
    def check(self, a):
        return CHECKS["no_fake_install_url"](a)

    def test_flags_hallucinated_flox_installers(self):
        for bad in (
            "curl -fsSL https://install.flox.dev | sh",
            "see flox.dev/install for details",
            "curl https://example.com/flox | bash",
        ):
            with self.subTest(bad=bad):
                self.assertFalse(self.check(bad))

    def test_allows_real_install_and_other_tool_curls(self):
        self.assertTrue(self.check("brew install flox"))
        self.assertTrue(self.check("curl -fsSL https://get.docker.com | sh"))


class TestInvokesFlox(unittest.TestCase):
    def check(self, a):
        return CHECKS["invokes_flox"](a)

    def test_true_when_flox_guidance_present(self):
        self.assertTrue(self.check("Run `flox init` then add python to [install]."))

    def test_false_when_flox_absent(self):
        self.assertFalse(self.check("Just run `npm init` and install node."))

    def test_false_on_bare_mention_without_guidance(self):
        self.assertFalse(self.check("Flox is a package manager."))


class TestTomlBlocks(unittest.TestCase):
    def test_captures_toml_and_bare_fences_only(self):
        self.assertIn("x = 1", toml_blocks("```toml\nx = 1\n```"))
        self.assertIn("y = 2", toml_blocks("```\ny = 2\n```"))
        # language-tagged non-toml blocks are intentionally out of scope
        self.assertEqual("", toml_blocks("```bash\nz=3\n```"))
        self.assertEqual("", toml_blocks("```python\nw=4\n```"))

    def test_captures_crlf_fences(self):
        # CRLF must not silently skip the block (that would disable every
        # manifest-scoped check on Windows-style answers).
        self.assertIn("x = 1", toml_blocks("```toml\r\nx = 1\r\n```"))
        self.assertIn("y = 2", toml_blocks("```\r\ny = 2\r\n```"))

    def test_captures_multiple_blocks(self):
        blocks = toml_blocks("```toml\na = 1\n```\ntext\n```toml\nb = 2\n```")
        self.assertIn("a = 1", blocks)
        self.assertIn("b = 2", blocks)


if __name__ == "__main__":
    unittest.main(verbosity=2)
