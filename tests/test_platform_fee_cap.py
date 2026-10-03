from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from eventyay_stripe.payment import StripeMethod


@pytest.mark.parametrize(
    ("prior_application_fee", "expected_fee"),
    [(75, Decimal("0.25")), (None, Decimal("0.75"))],
)
def test_business_fee_does_not_exceed_remaining_order_fee_cap(prior_application_fee, expected_fee):
    method = StripeMethod.__new__(StripeMethod)
    method.event = SimpleNamespace(organizer=object(), currency="EUR")
    method._amount_to_decimal = lambda cents: Decimal(cents) / 100
    payment = MagicMock(amount=Decimal("15.00"), pk=2)
    payment.order.total = Decimal("20.00")
    payment.order.positions.all.return_value = [
        SimpleNamespace(price=Decimal("20.00"), tax_value=Decimal("0.00")),
    ]
    payment.order.payments.filter.return_value.exclude.return_value = [
        SimpleNamespace(info_data={"application_fee_amount": prior_application_fee}),
    ]
    subscription_model = MagicMock()
    subscription_model.objects.filter.return_value.exclude.return_value.select_related.return_value.first.return_value = None

    with (
        patch("eventyay_stripe.payment.apps.is_installed", return_value=True),
        patch("eventyay_stripe.payment.apps.get_model", return_value=subscription_model),
        patch(
            "eventyay_stripe.payment.import_module",
            return_value=SimpleNamespace(
                resolve_fee_settings=MagicMock(return_value=(Decimal("10.00"), Decimal("1.00"), False))
            ),
        ),
    ):
        assert method._business_platform_fee(payment) == expected_fee
