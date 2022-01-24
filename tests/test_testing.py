# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
from textwrap import dedent

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


class MockRequirer(EndpointWrapper):
    ROLE = "requires"
    INTERFACE = "mock-rel"
    SCHEMA = _SCHEMA
    LIMIT = 1

    def __init__(self, *args):
        super().__init__(*args)
        self.auto_data = {self.charm.unit: {"request": "foo"}}


class MockProvider(testing.MockRemoteRelationMixin, EndpointWrapper):
    ROLE = "provides"
    INTERFACE = "mock-rel"
    SCHEMA = _SCHEMA


class MockRequirerCharm(CharmBase):
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
        self.rel = MockRequirer(self)


def test_mrrm(monkeypatch):
    harness = Harness(MockRequirerCharm, meta=MockRequirerCharm.META)
    provider = MockProvider(harness)

    harness.set_leader(False)
    harness.begin_with_initial_hooks()

    assert not harness.charm.rel.is_available()
    assert not harness.charm.rel.is_ready()

    relation = provider.relate()
    assert harness.charm.rel.is_available()
    assert not harness.charm.rel.is_ready()
    data = provider.unwrap(relation)
    assert data[harness.charm.unit] == {"request": "foo"}

    provider.wrap(relation, {provider.charm.app: {"response": "bar"}})
    assert harness.charm.rel.is_available()
    assert harness.charm.rel.is_ready()
    data = harness.charm.rel.unwrap(relation)
    assert data[provider.charm.app] == {"response": "bar"}
