"""Synthetic UPI message generator. No real people, numbers or messages.

Every template belongs to a family (scam or legit). The last two templates of
each family are reserved for the held-out set, so the held-out messages use
sentence shapes the model never saw in training.
"""
import random

NAMES = ["Aarav", "Meera", "Ravi", "Kavya", "Imran", "Priya", "Arjun", "Sneha", "Karthik", "Divya"]
SHOPS = ["Swiggy", "Zomato", "BigBasket", "Myntra", "Ola", "IRCTC", "Flipkart", "Blinkit"]
BANKS = ["SBI", "HDFC", "ICICI", "Axis", "Canara", "Kotak"]
DOMAINS = ["bit.ly/{r}", "tinyurl.com/{r}", "{r}-verify.xyz", "secure-{r}.top", "http://{r}.in/kyc", "cutt.ly/{r}"]


def _r(rng, n=6):
    return "".join(rng.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(n))


def _fill(t, rng):
    amt = rng.choice([49, 99, 199, 250, 480, 999, 1499, 2500, 4999, 9800, 15000, 49999])
    return t.format(
        name=rng.choice(NAMES), shop=rng.choice(SHOPS), bank=rng.choice(BANKS),
        amt=f"{amt:,}", link=rng.choice(DOMAINS).format(r=_r(rng)),
        upi=f"{rng.choice(NAMES).lower()}{rng.randint(10, 99)}@{rng.choice(['okaxis', 'ybl', 'paytm', 'oksbi', 'ibl'])}",
        ph=f"9{rng.randint(100000000, 999999999)}", ac=rng.randint(1000, 9999),
        hrs=rng.choice([2, 6, 12, 24]), ref=rng.randint(100000, 999999),
    )


SCAM = {
    "fake_refund": [
        "Your refund of Rs {amt} is ready. Approve the collect request from {upi} and enter your UPI PIN to receive it.",
        "{shop} refund pending. Accept the request sent to your UPI app and put your PIN to get Rs {amt} back.",
        "Excess payment of Rs {amt} will be returned. Tap approve on the request and enter PIN to receive money.",
        "Sorry for the failed order. To get your refund Rs {amt} scan this QR and enter UPI PIN.",
        "Refund initiated Rs {amt}. Kindly authorise the pending request {upi} with your PIN, else refund cancelled.",
        "Cashback Rs {amt} credited soon, accept collect request and type your secret PIN to claim it now.",
    ],
    "kyc_block": [
        "Dear customer your {bank} account will be blocked in {hrs} hours. Complete KYC now: {link}",
        "{bank} KYC expired. Update PAN and Aadhaar immediately at {link} or UPI will be suspended.",
        "Your UPI ID is suspended due to incomplete KYC. Click {link} and verify card details within {hrs} hrs.",
        "Urgent: account {ac} frozen. Verify your netbanking password here {link} to reactivate.",
        "Dear user, {bank} net banking is deactivated today. Share OTP and card number at {link} to restore.",
        "Last warning, KYC pending, your wallet limit will be cancelled. Download the update from {link}",
    ],
    "prize": [
        "Congratulations! You won Rs {amt} in the lucky draw. Pay Rs 99 processing fee to {upi} to claim your prize.",
        "KBC lottery winner! Your number won Rs {amt}. Contact {ph} and pay the tax fee to release the prize.",
        "You have been selected for a gift of Rs {amt}. Pay a small registration charge via UPI to receive it.",
        "Lucky customer! {shop} bumper reward Rs {amt}. Send a refundable deposit to {upi} to unlock your gift.",
        "Winner alert: claim your Rs {amt} voucher now at {link}, pay delivery fee only.",
        "Dear winner you won a free iPhone. Pay Rs {amt} courier cost to {upi} within {hrs} hours.",
    ],
    "job_task": [
        "Part time job, earn Rs {amt} daily by liking videos. Pay Rs 500 deposit to {upi} to start, money back with profit.",
        "Work from home, Rs {amt} per day. Join Telegram {ph}, first pay a small registration fee on UPI.",
        "Task income! Complete simple tasks and earn. Send refundable security deposit Rs {amt} to start today.",
        "Hiring data entry, no experience. Pay the training kit fee {amt} to {upi}, salary guaranteed.",
        "Invest Rs {amt} today and get double in {hrs} hours guaranteed returns. Transfer to {upi}.",
        "Earn from home liking products, you must first top up Rs {amt} to unlock the tasks, withdraw anytime.",
    ],
    "authority": [
        "Electricity board notice: power will be disconnected tonight 9.30pm. Pay Rs {amt} now to {upi} or call {ph}.",
        "Customs: your parcel is held. Pay Rs {amt} clearance fee to {upi} within {hrs} hours or legal action.",
        "This is cyber police. A case is filed on your Aadhaar. Pay Rs {amt} to {upi} to close it, do not tell anyone.",
        "RBI notice: pending penalty Rs {amt}. Pay immediately via {link} to avoid arrest.",
        "Your gas connection is cancelled. Update your bill with officer on {ph} and pay Rs {amt} today.",
        "Income tax department: refund of Rs {amt} blocked, pay the verification fee at {link} urgently.",
    ],
    "remote_access": [
        "Customer care here. To fix your failed payment install AnyDesk and share the 9 digit code with us.",
        "Your {bank} app has an issue. Download the support app from {link} and share the screen to resolve it.",
        "To cancel the wrong transfer of Rs {amt}, install QuickSupport and tell me the OTP that you receive.",
        "We are from {shop} helpline. Share your OTP so that we can reverse the charge of Rs {amt} immediately.",
        "Dear user kindly open the apk at {link} and allow all permissions to receive your pending cashback.",
        "Bank officer calling. Your card is misused, read out the OTP and card expiry to block the transaction.",
    ],
    "marketplace": [
        "I am the buyer for your OLX item. I sent Rs {amt}, just approve the request and enter PIN to receive it.",
        "Army officer here, want to buy your sofa. I will pay by UPI, scan this QR code to receive advance.",
        "Hello seller, payment of Rs {amt} sent by mistake, please accept the collect request to receive it.",
        "I will pay full amount now, you just need to scan my code and put your PIN for the token transfer.",
        "Interested in your scooter. For safety transfer Rs {amt} from your side first, I will return double.",
        "Sir I have sent Rs {amt} extra, return the difference to {upi} immediately, my family is waiting.",
    ],
}

LEGIT = {
    "bank_alert": [
        "Rs {amt} debited from A/c XX{ac} to {upi} on UPI Ref {ref}. If not you, call your bank helpline. - {bank}",
        "Rs {amt} credited to your A/c XX{ac} via UPI from {upi}. Ref {ref}. - {bank}",
        "{bank}: Your UPI payment of Rs {amt} to {shop} was successful. Ref no {ref}.",
        "UPI mandate of Rs {amt} for {shop} executed on your A/c XX{ac}. Manage it in your app.",
        "Alert: balance in A/c XX{ac} is low. Available balance Rs {amt}. - {bank}",
        "Dear customer, statement for A/c XX{ac} is ready in your {bank} app.",
    ],
    "otp": [
        "{ref} is your OTP for the transaction of Rs {amt} at {shop}. Do not share it with anyone. - {bank}",
        "Your login OTP is {ref}. Never share your OTP, {bank} will never ask for it.",
        "OTP {ref} for adding a new payee in {bank} app. Do not share. Valid for 10 minutes.",
        "Use {ref} to verify your mobile number on {shop}. Valid 5 minutes, do not share this code.",
        "{ref} is the code to reset your UPI PIN. Nobody from the bank will ask you for this, keep it safe.",
        "Your one time password {ref} expires in 5 minutes. Do not disclose it to anyone including staff.",
    ],
    "merchant": [
        "Your {shop} order #{ref} of Rs {amt} is confirmed and will arrive by 8 pm.",
        "Payment received: Rs {amt} paid to {shop}. Thanks for shopping with us!",
        "{shop}: Your delivery partner {name} is 5 minutes away with order #{ref}.",
        "Thank you for riding. Your trip fare is Rs {amt}, paid via UPI. Rate your trip.",
        "Your IRCTC ticket PNR {ref} is booked. Amount Rs {amt} was paid by UPI.",
        "Your {shop} subscription renews tomorrow for Rs {amt}. Cancel anytime from the app settings.",
    ],
    "friend": [
        "Hey it's {name}, can you send me Rs {amt} for dinner yesterday? I'll pay you back on Friday.",
        "Bro I paid for the movie tickets, your share is Rs {amt}. Send when free.",
        "Hi, rent for this month is Rs {amt}, I'll transfer to your account tonight.",
        "Thanks for the lunch {name}! Sending Rs {amt} now, please check.",
        "Mom here, transferred Rs {amt} for your books. Tell me if it did not reach.",
        "Can you split the cab fare? It was Rs {amt} in total, just send your half.",
    ],
    "genuine_refund": [
        "Refund of Rs {amt} for order #{ref} has been credited to your account. It may take 2 days to show.",
        "{shop}: Your refund Rs {amt} was processed to the original payment method. No action needed.",
        "Your cancelled ticket refund of Rs {amt} will reach your bank in 3 to 5 working days. No action is needed.",
        "We have credited Rs {amt} as a goodwill refund to your wallet. Nothing more is needed from you.",
        "Refund status for order #{ref}: completed. Rs {amt} is back in your account.",
        "Your {shop} refund has been issued. You do not need to share any details or approve anything.",
    ],
    "bill_reminder": [
        "Your electricity bill of Rs {amt} is due on the 15th. Pay on the official app or website to avoid late fee.",
        "Reminder: credit card bill Rs {amt} due in {hrs} days. Pay from your bank app.",
        "Your broadband plan expires soon. Recharge from the app to continue the service.",
        "Insurance premium of Rs {amt} falls due next week. Autopay is on for your account.",
        "Gas cylinder booked. Amount Rs {amt} to be paid on delivery to the delivery person.",
        "Your mobile postpaid bill Rs {amt} is generated. View it on the official app.",
    ],
    "promo": [
        "Flat 20% cashback on your next {shop} order above Rs {amt}. Offer valid till Sunday. T&C apply.",
        "{shop} sale starts tonight! Up to 60% off on top brands. Shop in the app.",
        "Get a Rs 50 reward when you pay your friends using UPI this week. Terms apply, see app.",
        "New feature: pay with UPI Lite on small payments. Learn more in your payments app.",
        "Your {bank} credit card has a new offer on dining. Check the offers tab in the app.",
        "Exclusive for you, {name}: invite friends to {shop} and both of you get a coupon.",
    ],
}

HELD = 2  # templates per family reserved for the held-out set


def _context(label, rng):
    """Behavioural context. Overlaps between classes on purpose (noisy)."""
    scam = label == 1
    unknown = rng.random() < (0.8 if scam else 0.25)
    collect = rng.random() < (0.55 if scam else 0.12)
    typical = rng.choice([300, 600, 1200, 2500])
    mult = rng.choice([0.3, 0.8, 1, 2, 4, 8]) if not scam else rng.choice([0.5, 1, 2, 5, 10, 20])
    return {
        "kind": "collect" if collect else rng.choice(["pay", "info", "info"]),
        "sender_known": not unknown,
        "payee_new": rng.random() < (0.7 if scam else 0.2),
        "amount": int(typical * mult), "typical_amount": typical,
        "hour": rng.choice([1, 3, 9, 11, 14, 18, 21, 23]) if scam else rng.choice([8, 9, 11, 13, 15, 18, 20, 22, 2]),
        "account_age_days": rng.choice([10, 20, 90, 400, 900]) if scam else rng.choice([15, 90, 400, 900, 1500]),
    }


def _mutate(t, rng):
    if rng.random() < 0.25:
        t = t.lower()
    if rng.random() < 0.15:
        t = t.replace("your", "ur").replace("please", "pls")
    if rng.random() < 0.10 and len(t) > 20:
        i = rng.randrange(5, len(t) - 5)
        t = t[:i] + t[i + 1:]
    return t


def generate(n, seed, split="train", scam_ratio=0.4):
    """split: train (older templates), heldout (reserved templates), or all."""
    rng = random.Random(seed)
    pools = []
    for label, fams in ((1, SCAM), (0, LEGIT)):
        for fam, temps in fams.items():
            if split == "train":
                use = temps[:-HELD]
            elif split == "heldout":
                use = temps[-HELD:]
            else:
                use = temps
            pools.append((label, fam, use))
    scam_pools = [p for p in pools if p[0] == 1]
    legit_pools = [p for p in pools if p[0] == 0]
    out = []
    for i in range(n):
        label = 1 if rng.random() < scam_ratio else 0
        _, fam, temps = rng.choice(scam_pools if label else legit_pools)
        text = _mutate(_fill(rng.choice(temps), rng), rng)
        out.append({"id": f"{split}-{seed}-{i}", "text": text, "label": label, "family": fam, "context": _context(label, rng)})
    return out
