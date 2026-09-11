from __future__ import annotations

import time
from importlib import import_module

import pytest

from app.core.config import InsecureConfigurationError, Settings, get_settings
from app.entitlement import Plan, resolve
from app.entitlement.resolve import TRIAL_DAYS, fim_do_trial

resolve_mod = import_module("app.entitlement.resolve")

DIA = 86400.0
TRIAL = TRIAL_DAYS * DIA


class TestAncora:
    def test_trial_gasto_antes_da_cerca_recomeca_quando_ela_sobe(self):
        qualificou = 1_700_000_000.0
        cerca = qualificou + 200 * DIA

        fim = fim_do_trial(qualificou, qualificou + TRIAL, cerca)

        assert fim == cerca + TRIAL, (
            "quem já tinha carteira precisa dos 14 dias a partir da cerca — o trial que "
            "correu enquanto nada era cercado não foi um trial"
        )

    def test_quem_qualifica_depois_da_cerca_conta_do_proprio_momento(self):
        cerca = 1_700_000_000.0
        qualificou = cerca + 30 * DIA

        fim = fim_do_trial(qualificou, qualificou + TRIAL, cerca)

        assert fim == qualificou + TRIAL, (
            "depois da cerca o relógio é o da própria conta, e coincide com o gravado"
        )

    def test_sem_carteira_nao_ha_trial_para_ancorar(self):
        cerca = 1_700_000_000.0

        assert fim_do_trial(None, None, cerca) is None

    def test_sem_data_de_cerca_o_valor_gravado_prevalece(self):
        qualificou = 1_700_000_000.0

        assert fim_do_trial(qualificou, qualificou + TRIAL, None) == qualificou + TRIAL


class TestResolveComACercaLigada:
    @pytest.fixture()
    def cerca(self, monkeypatch):
        settings = get_settings()
        monkeypatch.setattr(settings, "entitlements_enabled", True, raising=False)
        monkeypatch.setattr(resolve_mod, "_ainda_nao_comecou", lambda _user_id: False)
        return settings

    def _assinatura(self, user_id: str, trial_started_at: float):
        from app.core.database import db_session
        from app.models.db_models import SubscriptionDb

        with db_session() as session:
            row = session.get(SubscriptionDb, user_id)
            if row is None:
                row = SubscriptionDb(user_id=user_id)
                session.add(row)
            row.status = "trialing"
            row.trial_started_at = trial_started_at
            row.trial_ends_at = trial_started_at + TRIAL

    def test_conta_antiga_nao_cai_para_free_ao_ligar_a_cerca(self, cerca, monkeypatch):
        agora = time.time()
        self._assinatura("trial_queimado", agora - 300 * DIA)
        monkeypatch.setattr(cerca, "entitlements_enabled_at", str(agora - DIA), raising=False)

        direitos = resolve("trial_queimado", now=agora)

        assert direitos.plan is Plan.PREMIUM, (
            "este é o alçapão: sem âncora a conta viraria Free no instante em que a cerca acende"
        )
        assert direitos.in_trial is True
        assert direitos.days_left_in_trial is not None
        assert direitos.days_left_in_trial >= TRIAL_DAYS - 2

    def test_sem_ancora_a_mesma_conta_cai_para_free(self, cerca, monkeypatch):
        agora = time.time()
        self._assinatura("trial_queimado_sem_ancora", agora - 300 * DIA)
        monkeypatch.setattr(cerca, "entitlements_enabled_at", "", raising=False)

        direitos = resolve("trial_queimado_sem_ancora", now=agora)

        assert direitos.plan is Plan.FREE
        assert direitos.in_trial is False

    def test_trial_ancorado_tambem_expira(self, cerca, monkeypatch):
        agora = time.time()
        cerca_subiu = agora - 100 * DIA
        self._assinatura("trial_ancorado_vencido", cerca_subiu - 50 * DIA)
        monkeypatch.setattr(cerca, "entitlements_enabled_at", str(cerca_subiu), raising=False)

        direitos = resolve("trial_ancorado_vencido", now=agora)

        assert direitos.plan is Plan.FREE
        assert direitos.in_trial is False


class TestFalhaAlto:
    def test_cerca_ligada_sem_data_derruba_o_startup(self):
        settings = Settings(
            app_env="production",
            jwt_secret="um-segredo-de-verdade",
            allowed_origins="https://exemplo.com",
            billing_webhook_secret="outro-segredo",
            entitlements_enabled=True,
            entitlements_enabled_at="",
        )

        with pytest.raises(InsecureConfigurationError, match="ENTITLEMENTS_ENABLED_AT"):
            settings.validate_for_startup()

    def test_data_que_nao_e_data_tambem_derruba(self):
        settings = Settings(
            app_env="production",
            jwt_secret="um-segredo-de-verdade",
            allowed_origins="https://exemplo.com",
            billing_webhook_secret="outro-segredo",
            entitlements_enabled=True,
            entitlements_enabled_at="quinta-feira",
        )

        with pytest.raises(InsecureConfigurationError, match="ENTITLEMENTS_ENABLED_AT"):
            settings.validate_for_startup()

    def test_cerca_ligada_com_data_iso_sobe(self):
        settings = Settings(
            app_env="production",
            jwt_secret="um-segredo-de-verdade",
            allowed_origins="https://exemplo.com",
            billing_webhook_secret="outro-segredo",
            entitlements_enabled=True,
            entitlements_enabled_at="2026-10-01",
        )

        settings.validate_for_startup()

        assert settings.entitlements_up_at == pytest.approx(1_790_812_800.0)

    def test_cerca_desligada_nao_exige_data(self):
        settings = Settings(
            app_env="production",
            jwt_secret="um-segredo-de-verdade",
            allowed_origins="https://exemplo.com",
            billing_webhook_secret="outro-segredo",
            entitlements_enabled=False,
        )

        settings.validate_for_startup()

    def test_epoch_e_iso_com_fuso_sao_aceitos(self):
        assert Settings(entitlements_enabled_at="1790812800").entitlements_up_at == 1_790_812_800.0
        assert Settings(
            entitlements_enabled_at="2026-10-01T00:00:00Z"
        ).entitlements_up_at == pytest.approx(1_790_812_800.0)
