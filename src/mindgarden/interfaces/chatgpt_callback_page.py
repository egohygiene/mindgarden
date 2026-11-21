"""Render the local ChatGPT callback with fixed copy and a hashed stylesheet."""

from base64 import b64encode
from hashlib import sha256


_STYLE = """
:root {
  color-scheme: light;
  font-family: system-ui, -apple-system, sans-serif;
  color: #203229;
  background: #f2f4ec;
}
* { box-sizing: border-box; }
body {
  min-height: 100vh;
  min-height: 100svh;
  display: grid;
  place-items: center;
  margin: 0;
  padding: clamp(16px, 5vw, 56px);
  background: radial-gradient(ellipse at 52% 12%, #e2edda, #f2f4ec 67%);
}
.card {
  width: min(100%, 650px);
  overflow: hidden;
  border: 1px solid #d6ddd1;
  border-radius: 22px;
  background: #fcfdf8;
  box-shadow: 0 23px 60px #14241c16;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: clamp(19px, 4vw, 26px) clamp(22px, 5vw, 40px);
  background: radial-gradient(ellipse at 92% 130%, #3f6447, #14241c 65%);
  color: #f7f8ef;
  font: 600 1.37rem/1.2 Georgia, serif;
  letter-spacing: -.04em;
}
.mark {
  position: relative;
  width: 39px;
  height: 39px;
  flex: 0 0 39px;
  border-radius: 11px;
  background: #c7e87f;
  color: #233d29;
}
.mark::before, .mark::after, .stem {
  position: absolute;
  display: block;
}
.mark::before, .mark::after {
  top: 11px;
  width: 11px;
  height: 8px;
  border: 2px solid currentColor;
  content: "";
}
.mark::before {
  left: 8px;
  border-radius: 3px 10px 3px 10px;
  transform: rotate(16deg);
}
.mark::after {
  right: 8px;
  border-radius: 10px 3px 10px 3px;
  transform: rotate(-16deg);
}
.stem {
  width: 2px;
  height: 11px;
  top: 18px;
  left: 18.5px;
  background: currentColor;
  border-radius: 2px;
}
.content { padding: clamp(24px, 5vw, 44px) clamp(22px, 5vw, 40px); }
.label {
  margin: 0 0 10px;
  color: #386148;
  font-size: .8rem;
  font-weight: 750;
  letter-spacing: .04em;
}
h1 {
  max-width: 19ch;
  margin: 0 0 12px;
  font: 600 clamp(2rem, 5.9vw, 3.15rem)/1.05 Georgia, serif;
  letter-spacing: -.045em;
}
.lead, .next p, .close {
  margin: 0;
  color: #52665a;
  line-height: 1.55;
}
.next {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  align-items: start;
  gap: 11px;
  margin-top: 24px;
  border: 1px solid #d6ddd1;
  border-radius: 11px;
  background: #eef4e9;
  padding: 13px;
}
.arrow {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 8px;
  color: #386148;
  background: #dcead1;
}
.arrow::before {
  width: 8px;
  height: 8px;
  border-top: 2px solid currentColor;
  border-right: 2px solid currentColor;
  content: "";
  transform: translateX(-2px) rotate(45deg);
}
.next h2 { margin: 2px 0 4px; font-size: .98rem; }
.next p, .close { font-size: .89rem; }
.close { margin-top: 15px; }
@media (forced-colors: active) {
  .mark, .arrow { border: 1px solid currentColor; }
  .stem { background: currentColor; forced-color-adjust: none; }
}
"""

CALLBACK_STYLE_POLICY = (
    "style-src 'sha256-"
    + b64encode(sha256(_STYLE.encode("utf-8")).digest()).decode("ascii")
    + "'"
)

_OUTCOMES = {
    "received": (
        "Sign-in response received",
        "Mindgarden is checking the response from ChatGPT.",
    ),
    "declined": (
        "Sign-in permission declined",
        "You can start a new sign-in when you’re ready.",
    ),
    "invalid": (
        "Sign-in response could not be verified",
        "Mindgarden could not finish this step.",
    ),
}

_NEXT_STEPS = {
    "studio": (
        "Return to Models",
        "Go back to Models in the original Mindgarden Studio tab to see the sign-in status.",
    ),
    "terminal": (
        "Return to your terminal",
        "Go back to the terminal where you started Mindgarden sign-in to see the result.",
    ),
}


def callback_page(destination: str, outcome: str) -> bytes:
    """Build one of the six pages without using callback request data."""
    try:
        title, summary = _OUTCOMES[outcome]
        action, instructions = _NEXT_STEPS[destination]
    except (KeyError, TypeError):
        raise ValueError("Unsupported callback page variant") from None
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Return to Mindgarden</title>
  <style>{_STYLE}</style>
</head>
<body>
  <main class="card" aria-labelledby="callback-title">
    <header class="brand">
      <span class="mark" aria-hidden="true"><span class="stem"></span></span>
      <span>Mindgarden</span>
    </header>
    <div class="content">
      <p class="label">ChatGPT sign-in</p>
      <h1 id="callback-title">{title}</h1>
      <p class="lead">{summary}</p>
      <section class="next" aria-labelledby="next-title">
        <span class="arrow" aria-hidden="true"></span>
        <div>
          <h2 id="next-title">{action}</h2>
          <p>{instructions}</p>
        </div>
      </section>
      <p class="close">You can close this tab.</p>
    </div>
  </main>
</body>
</html>
""".encode("utf-8")
