"""Strict anonymous discovery-input boundary, independent of private generation."""
from Discovery import estimated_noise1_schema as schema


def discovery_payload(public, policy):
    schema.validate(public, schema.PUBLIC)
    schema.validate(policy, schema.POLICY)
    return {**public, 'policy': policy}
