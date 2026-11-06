"""Validated design source and small deterministic, replaceable consumers."""

from pathlib import Path
import json
import sys

from .contracts import ContractRegistry, read_object
from .validation import ContractError


def design_directory():
    for path in (Path(__file__).resolve().parents[3] / "design", Path(sys.prefix) / "share/mindgarden/design"):
        if (path / "tokens/mindgarden.tokens.json").is_file():
            return path
    raise ContractError("DESIGN_UNAVAILABLE: install the complete design resources")


def luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    channels = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return sum(value * weight for value, weight in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast(first, second):
    values = sorted((luminance(first), luminance(second)))
    return (values[1] + 0.05) / (values[0] + 0.05)


def validate_tokens(tokens):
    registry = ContractRegistry(design_directory() / "schemas")
    if registry.errors(tokens, "urn:egohygiene:mindgarden:design-tokens:v1"):
        raise ContractError("DESIGN_TOKENS: tokens violate the supported design contract")
    for colors in tokens["colors"].values():
        for background in ("background", "surface"):
            if any(contrast(colors[field], colors[background]) < 4.5 for field in ("text", "muted", "accent")):
                raise ContractError("DESIGN_CONTRAST: text/link colors require at least 4.5:1 contrast")
            if any(contrast(colors[field], colors[background]) < 3 for field in ("border", "focus")):
                raise ContractError("DESIGN_CONTRAST: focus/control boundaries require at least 3:1 contrast")
    return tokens


def load_tokens(path=None):
    return validate_tokens(read_object(path or design_directory() / "tokens/mindgarden.tokens.json"))


def font_family(values):
    generic = {"system-ui", "sans-serif", "serif", "monospace", "ui-monospace", "ui-sans-serif"}
    return ", ".join(value if value in generic else json.dumps(value) for value in values)


def quartz_theme(tokens):
    tokens = validate_tokens(tokens)
    result = {}
    for mode, colors in tokens["colors"].items():
        result[mode + "Mode"] = {"light": colors["background"], "lightgray": colors["surface"], "gray": colors["muted"],
            "darkgray": colors["text"], "dark": colors["text"], "secondary": colors["accent"], "tertiary": colors["focus"],
            "highlight": colors["accent"] + "22", "textHighlight": colors["accent"] + "33"}
    return result


def css_variables(tokens):
    tokens = validate_tokens(tokens)
    def colors(mode):
        return "".join("--mg-" + key + ":" + value + ";" for key, value in tokens["colors"][mode].items())
    typography = tokens["typography"]
    base = "".join("--mg-space-" + key + ":" + str(value) + "px;" for key, value in tokens["spacing"].items())
    for group in ("borders", "effects", "layout"):
        for key, value in tokens[group].items():
            base += "--mg-" + key.replace("_", "-") + ":" + str(value) + ("px" if key.endswith("_px") else "") + ";"
    base += "--mg-body-font:" + font_family(typography["body_family"]) + ";--mg-heading-font:" + font_family(typography["heading_family"]) + ";--mg-code-font:" + font_family(typography["code_family"]) + ";"
    return (":root{" + base + colors("light") + "}\n@media(prefers-color-scheme:dark){:root{" + colors("dark") + "}}\n"
            + ':root[saved-theme="light"]{' + colors("light") + '}\n:root[saved-theme="dark"]{' + colors("dark") + "}\n")


def quartz_styles(tokens):
    tokens = validate_tokens(tokens)
    typography, layout, borders = (tokens[key] for key in ("typography", "layout", "borders"))
    return css_variables(tokens) + f"""
:root {{ --bodyFont: var(--mg-body-font); --headerFont: var(--mg-heading-font); --codeFont: var(--mg-code-font); }}
body {{ font-family:var(--mg-body-font); font-size:{typography['body_px']}px; background:var(--mg-background); color:var(--mg-text); }}
h1,h2,h3,.page-title {{ font-family:var(--mg-heading-font); }}
.page-title {{ letter-spacing:{typography['display_tracking_em']}em; overflow-wrap:anywhere; }}
code,pre {{ font-family:var(--mg-code-font); }}
a {{ color:var(--mg-accent); text-underline-offset:.2em; }}
article,.center {{ min-width:0; max-width:100%; }}
article pre,article pre code,.code-wrapper {{ max-width:100%; white-space:pre-wrap; overflow-wrap:anywhere; }}
article pre code {{ display:block; width:100%; }}
article pre,article pre code,article pre code span {{ color:var(--mg-text)!important; background:var(--mg-surface)!important; }}
button,input,summary {{ min-height:{layout['touch_target_px']}px; }}
button {{ min-width:{layout['touch_target_px']}px; }}
button,input {{ border-color:var(--mg-border); }}
:focus-visible {{ outline:{borders['focus_px']}px solid var(--mg-focus); outline-offset:3px; }}
#mindgarden-graph {{ border-radius:{borders['radius_px']}px; border-color:var(--mg-border); background:var(--mg-surface); }}
#mindgarden-graph button {{ background:var(--mg-surface); color:var(--mg-text); border:1px solid var(--mg-border); border-radius:4px; }}
@media(max-width:{layout['mobile_breakpoint_px']}px) {{
 .page {{ box-sizing:border-box; width:100%; max-width:100%; padding-inline:{tokens['spacing']['md']}px; }}
 .page>#quartz-body {{ box-sizing:border-box; display:flex; flex-direction:column; min-width:0; width:100%; max-width:100%; padding:0; }}
 .page>#quartz-body>.sidebar.left {{ position:relative; top:auto; display:flex; flex-flow:row wrap; align-items:center; width:100%; height:auto; min-height:0; padding:0; margin:0; gap:8px; }}
 .page>#quartz-body>.sidebar.left .explorer {{ flex-basis:100%; min-width:0; max-width:100%; }}
 .explorer.collapsed,.explorer:not(.collapsed) {{ flex:1 1 100%; }}
 .explorer .explorer-content {{ position:relative; width:100%; max-width:100%; height:auto; max-height:40vh; padding:0; transform:none; overflow:auto; }}
 .explorer.collapsed>.explorer-content {{ display:none; }}
 .explorer:not(.collapsed)>.explorer-content {{ display:block; visibility:visible; }}
 .page>#quartz-body>.center {{ width:100%; padding:0; min-width:0; }}
 .page>#quartz-body>.sidebar.right {{ display:none; }}
}}
@media(prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ animation:none!important; transition:none!important; scroll-behavior:auto!important; }} }}
"""
