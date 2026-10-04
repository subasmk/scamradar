"""Behavioural signals from the payment context, not the words."""


def score_behaviour(ctx):
    """ctx keys: kind, sender_known, payee_new, amount, typical_amount, hour, account_age_days."""
    s, why = 0.0, []
    if ctx.get("kind") == "collect" and not ctx.get("sender_known", True):
        s += 0.4
        why.append("A request for money from someone not in your contacts.")
    elif ctx.get("kind") == "collect":
        s += 0.1
    if not ctx.get("sender_known", True):
        s += 0.1
    if ctx.get("payee_new"):
        s += 0.15
        why.append("This would be your first payment to this payee.")
    typical = max(1, ctx.get("typical_amount", 1000))
    amount = ctx.get("amount", 0)
    if amount >= 5 * typical:
        s += 0.25
        why.append("The amount is much larger than you usually pay.")
    elif amount >= 3 * typical:
        s += 0.12
    if ctx.get("hour", 12) in (0, 1, 2, 3, 4, 5):
        s += 0.1
        why.append("It arrived in the middle of the night.")
    if ctx.get("account_age_days", 9999) < 30:
        s += 0.1
        why.append("Your UPI account is new, and new users are often targeted.")
    return min(1.0, s), why
