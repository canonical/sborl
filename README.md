# sborl - Schema-based Operator Relation Libraries

This library provides a base for creating relation endpoint libraries for use
with [charmed operators and Juju][charms]. It tries to make creating Pythonic
implementations of a relation interface protocol straightforward and
approachable, while encouraging good patterns such as using schema-based
interface protocol validation, providing helpers for testing charms using
your library, and surfacing problems with relations in a clean way.


# Example

An example endpoint class and usage might look like:

```python
class RandomURLRequirer(sborl.relation.EndpointWrapper):
    INTERFACE = "random-url"
    ROLE = "requires"
    SCHEMA = Path(__file__) / "schema.yaml"
    LIMIT = 1

    @property
    def url(self):
        if not self.is_ready():
            return None
        relation = self.relations[0]
        return self.unwrap(relation)[relation.app]["url"]


class MyCharm(ops.charm.CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.random_url = RandomURLRequirer(charm=self, endpoint="random-url-provider")
        self.framework.observe(self.random_url.on.ready, self._log_url)

    def _log_url(self, event):
        log.info(f"Got random URL: {self.random_url.url}")
```


[charms]: https://juju.is/docs
