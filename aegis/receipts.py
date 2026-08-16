from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class OutcomeReceipt:
    receipt_id: str
    generated_at: str
    payload: dict[str, Any]
    digest: str
    signature: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "generated_at": self.generated_at,
            "payload": self.payload,
            "digest": self.digest,
            "signature": self.signature,
        }


def create_receipt(payload: dict[str, Any], signing_key: str | None = None) -> OutcomeReceipt:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    signature = None
    if signing_key:
        signature = hmac.new(signing_key.encode(), canonical, hashlib.sha256).hexdigest()
    return OutcomeReceipt(
        receipt_id=f"sha256:{digest[:20]}",
        generated_at=datetime.now(timezone.utc).isoformat(),
        payload=payload,
        digest=digest,
        signature=signature,
    )


def verify_receipt(receipt: OutcomeReceipt, signing_key: str | None = None) -> bool:
    expected = create_receipt(receipt.payload, signing_key)
    digest_valid = hmac.compare_digest(receipt.digest, expected.digest)
    if signing_key:
        return digest_valid and bool(receipt.signature) and hmac.compare_digest(receipt.signature, expected.signature or "")
    return digest_valid
