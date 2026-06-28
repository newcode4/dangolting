"""CRM 설정 테스트."""
from utils.crm_config import daily_digest_hour, sla_unpaid_hours
from utils.crm_truth import DEFAULT_SLA_UNPAID_HOURS


def test_sla_defaults_without_secrets():
    assert sla_unpaid_hours() == DEFAULT_SLA_UNPAID_HOURS
    assert daily_digest_hour() == 12
