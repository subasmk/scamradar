"""Rule layer. Each rule carries a weight and a plain-language reason."""
import re

# (name, regex, weight, reason shown to the user)
RULES = [
    ("pin_to_receive", r"(enter|put|type|share|give)\w*.{0,30}(upi )?(pin|secret pin)|(pin).{0,25}(to receive|to get|to claim)",
     0.75, "It asks you to enter your UPI PIN. You never need a PIN to receive money."),
    ("approve_to_receive", r"(approve|accept|authori[sz]e|tap approve).{0,40}(request|collect).{0,60}(receive|get|refund|claim)|(refund|receive|get).{0,50}(approve|accept|authori[sz]e).{0,25}(request|collect)",
     0.6, "It says to approve a request in order to receive money. Approving a request sends money out."),
    ("scan_to_receive", r"scan.{0,30}(qr|code).{0,50}(receive|refund|advance|pin)",
     0.55, "Scanning a QR code is only for paying. It cannot bring money in."),
    ("share_otp", r"(share|tell|read out|disclose|give|send).{0,25}(otp|one time password|card number|card expiry|cvv|netbanking password)(?!.{0,20}(never|nobody))",
     0.6, "It asks for an OTP or card detail. Real banks never ask for these."),
    ("remote_app", r"(anydesk|quicksupport|teamviewer|screen ?share|share the screen|\.apk|open the apk|download the (update|support app))",
     0.7, "It asks you to install an app or share your screen. That gives a stranger control of your phone."),
    ("advance_fee", r"(pay|send|transfer).{0,40}(processing|registration|clearance|delivery|courier|tax|verification|training kit|security deposit|refundable|deposit)\w*.{0,25}(fee|charge|cost|deposit)?|(registration|processing|courier|clearance|verification) (fee|charge|cost)",
     0.45, "It asks for a small fee before you get something. Real prizes and refunds do not cost money first."),
    ("prize", r"(you won|you have won|winner|lucky draw|lottery|kbc|selected for a gift|free iphone|congratulations)",
     0.4, "It says you won something you never entered for."),
    ("urgent_threat", r"(within \d+ ?(hours|hrs)|immediately|tonight|urgent|last warning|will be (blocked|suspended|cancelled|disconnected|deactivated)|legal action|arrest|account .{0,10}(frozen|blocked))",
     0.35, "It pushes you to act fast or threatens you."),
    ("kyc_link", r"(kyc|aadhaar|pan).{0,50}(link|click|update|verify|download)|(click|verify|update).{0,40}(kyc)",
     0.45, "It asks for KYC or ID details through a message. Banks do this inside their own app."),
    ("odd_link", r"(bit\.ly|tinyurl|cutt\.ly|[a-z0-9-]+\.(xyz|top|tk)\b|http://)",
     0.4, "It has a shortened or unusual link."),
    ("authority", r"(cyber police|customs|rbi notice|income tax department|electricity board notice|officer)",
     0.3, "It claims to be an official body and asks for money."),
    ("double_money", r"(double|guaranteed|daily|per day).{0,30}(return|earn|income|profit|salary)|(earn|get double)|(refundable|money back).{0,25}profit",
     0.5, "It promises easy or guaranteed money."),
    ("secrecy", r"(do not tell anyone|don't tell anyone|dont tell anyone|keep (this )?secret)",
     0.5, "It tells you to keep this secret."),
    ("return_extra", r"(sent|paid).{0,15}(extra|by mistake).{0,60}(return|accept)|(return|send back).{0,25}(difference|extra)",
     0.45, "It claims a mistaken payment and asks you to act on it."),
]

# Phrases that usually mean the message is genuine and warns you.
SAFE = [
    ("warns_otp", r"(do not share|never share|will never ask|nobody .{0,20}will ask|do not disclose)", 0.45),
    ("no_action", r"(no action (is )?needed|you do not need to|nothing more is needed|credited to your|has been credited|processed to the original)", 0.35),
    ("bank_format", r"(a/c xx\d{4}|ref(erence)? ?(no)?\.? ?\d{5,}|debited from|credited to your a/c)", 0.3),
    ("in_app", r"(official app|in (the|your) .{0,15}app|from the (bank )?app|from your bank app|in your app)", 0.25),
]

_COMPILED = [(n, re.compile(p, re.I), w, r) for n, p, w, r in RULES]
_SAFE = [(n, re.compile(p, re.I), w) for n, p, w in SAFE]


def score_rules(text):
    """Return (score 0..1, hits[list of dict], safe_hits[list of names])."""
    hits = []
    keep = 1.0
    for name, rx, w, reason in _COMPILED:
        if rx.search(text):
            hits.append({"rule": name, "weight": w, "reason": reason})
            keep *= 1 - w
    pos = 1 - keep
    safe_hits = []
    keep_safe = 1.0
    for name, rx, w in _SAFE:
        if rx.search(text):
            safe_hits.append(name)
            keep_safe *= 1 - w
    score = max(0.0, pos * (0.35 + 0.65 * keep_safe) if safe_hits else pos)
    return score, hits, safe_hits
