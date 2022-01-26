# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
from textwrap import dedent

import pytest
from ops.charm import CharmBase
from ops.testing import Harness

from sborl import EndpointWrapper, testing


_SCHEMA = {
    "v1": {
        "requires": {
            "unit": {
                "type": "object",
                "properties": {
                    "request": {"type": "string"},
                },
                "required": ["request"],
            },
        },
        "provides": {
            "app": {
                "type": "object",
                "properties": {
                    "response": {"type": "string"},
                },
                "required": ["response"],
            },
        },
    },
}


class Provider(EndpointWrapper):
    ROLE = "provides"
    INTERFACE = "mock-rel"
    SCHEMA = _SCHEMA


class MockProvider(testing.MockRemoteRelationMixin, Provider):
    pass


class ProviderCharm(CharmBase):
    META = dedent(
        """\
        name: mock-rel-local
        provides:
          mock-rel:
            interface: mock-rel
        """
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rel = Provider(self)


class Requirer(EndpointWrapper):
    ROLE = "requires"
    INTERFACE = "mock-rel"
    SCHEMA = _SCHEMA
    LIMIT = 1


class MockRequirer(testing.MockRemoteRelationMixin, Requirer):
    pass


class RequirerCharm(CharmBase):
    META = dedent(
        """\
        name: mock-rel-local
        requires:
          mock-rel:
            interface: mock-rel
            limit: 1
        """
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rel = Requirer(self)


@pytest.mark.parametrize("role", ["provides", "requires"])
def test_mrrm(role):
    if role == "provides":
        harness = Harness(ProviderCharm, meta=ProviderCharm.META)
        harness.begin_with_initial_hooks()
        provider = harness.charm.rel
        requirer = MockRequirer(harness)
        local, remote = provider, requirer
    elif role == "requires":
        harness = Harness(RequirerCharm, meta=RequirerCharm.META)
        harness.begin_with_initial_hooks()
        provider = MockProvider(harness)
        requirer = harness.charm.rel
        local, remote = requirer, provider

    assert not provider.is_available()
    assert not provider.is_ready()
    assert not requirer.is_available()
    assert not requirer.is_ready()

    relation = remote.relate()
    # mock remote is always leader, so their versions will be sent to the local charm
    assert local.is_available()
    assert not local.is_ready()
    # local charm under test is not leader yet, so its will not be sent to the remote
    assert not remote.is_available()
    assert not remote.is_ready()

    harness.set_leader(True)
    assert provider.is_available()
    assert not provider.is_ready()
    assert requirer.is_available()
    assert not requirer.is_ready()

    requirer.wrap(relation, {requirer.unit: {"request": "foo"}})
    assert provider.is_available()
    assert provider.is_ready()
    assert requirer.is_available()
    assert not requirer.is_ready()

    data = provider.unwrap(relation)
    assert data[requirer.unit] == {"request": "foo"}

    provider.wrap(relation, {provider.app: {"response": "bar"}})
    assert provider.is_available()
    assert provider.is_ready()
    assert requirer.is_available()
    assert requirer.is_ready()
    data = requirer.unwrap(relation)
    assert data[provider.app] == {"response": "bar"}
