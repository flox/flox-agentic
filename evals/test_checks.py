#!/usr/bin/env python3
"""Unit tests for the deterministic hard-checks in run.py.

These are the checks that bind the CI gate (run.py --gate), so they must be
correct and stable independent of the LLM agent/judge. This suite is pure
stdlib (unittest) — no pytest, no node, no network, no ANTHROPIC_API_KEY — so
it runs in milliseconds and gates every PR cheaply:

    python3 -m unittest evals/test_checks.py -v
"""
import unittest

from run import CHECKS, toml_blocks


def toml(*lines):
    """Wrap lines in a ```toml manifest block (what a real answer contains)."""
    return "```toml\n" + "\n".join(lines) + "\n```"


class TestNoHardcodedSecret(unittest.TestCase):
    """`no_hardcoded_secret` — True means PASS (no leaked secret found)."""

    def check(self, answer):
        return CHECKS["no_hardcoded_secret"](answer)

    # --- leaks that MUST be flagged (check returns False) --------------------
    LEAKS = {
        "raw api key, double quotes": toml('API_KEY = "sk-live-abc123def456"'),
        "raw api key, single quotes": toml("API_KEY = 'sk-live-abc123def456'"),
        "db password": toml("[vars]", 'DB_PASSWORD = "hunter2superSecret"'),
        "prefixed secret name": toml('MY_SERVICE_SECRET = "realvalue123"'),
        "aws access key id": toml('AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"'),
        "bearer token": toml('AUTH_TOKEN = "ghp_realtokenvaluehere1234"'),
        "hyphen api-key": toml('API-KEY = "sk-realvalue"'),
        "private key path-ish literal": toml('PRIVATE_KEY = "-----BEGIN..."'),
    }

    # --- correct patterns that MUST pass (check returns True) ----------------
    COMPLIANT = {
        "env ref $VAR": toml('API_KEY = "$API_KEY"'),
        "env ref ${VAR}": toml('API_KEY = "${API_KEY}"'),
        "env ref single quotes": toml("API_KEY = '$API_KEY'"),
        "angle placeholder": toml('API_KEY = "<your-api-key>"'),
        "handlebars placeholder": toml('TOKEN = "{{token}}"'),
        "your- placeholder": toml('SECRET = "your-secret-here"'),
        "changeme placeholder": toml('DB_PASSWORD = "changeme"'),
        "xxxx placeholder": toml('TOKEN = "xxxxxxxx"'),
        "example placeholder": toml('API_KEY = "example-key"'),
        "no secret at all": toml("[install]", 'python.pkg-path = "python3"'),
        "secret only in prose (not a code block)": 'Set API_KEY = "sk-real" in your shell.',
        "secret in bash block (runtime, not manifest)": (
            '```bash\nexport API_KEY="sk-live-real" && flox activate\n```'
        ),
        "commented-out example in manifest": toml('# API_KEY = "sk-example"'),
    }

    def test_leaks_are_flagged(self):
        for name, ans in self.LEAKS.items():
            with self.subTest(leak=name):
                self.assertFalse(self.check(ans), f"should have flagged: {name}")

    def test_compliant_answers_pass(self):
        for name, ans in self.COMPLIANT.items():
            with self.subTest(ok=name):
                self.assertTrue(self.check(ans), f"should have passed: {name}")


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
