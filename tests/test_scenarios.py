import json
import unittest
from datetime import datetime
from ipaddress import ip_address, ip_network
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = ROOT / "data" / "scenarios"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "expected_scenarios.json"

EXPECTED_SCENARIO_IDS = {"scenario-a", "scenario-b"}
SCENARIO_FIELDS = {
    "id",
    "title",
    "description",
    "synthetic",
    "events",
    "processes",
    "connections",
    "deployments",
}
EVENT_FIELDS = {"id", "timestamp", "host", "source", "event_type", "message"}
PROCESS_FIELDS = {"pid", "host", "user", "command", "parent_pid", "started_at", "event_ids"}
CONNECTION_FIELDS = {"id", "host", "pid", "remote_ip", "remote_port", "timestamp", "event_ids"}
DEPLOYMENT_FIELDS = {"id", "host", "timestamp", "description", "event_ids"}
FORBIDDEN_SCENARIO_TERMS = {
    "attack",
    "malicious",
    "benign scenario",
    "expected incident",
    "expected classification",
    "compromise",
    "compromiso",
    "incidente esperado",
    "clasificacion esperada",
    "clasificación esperada",
}
DOCUMENTATION_NETWORKS = (
    ip_network("192.0.2.0/24"),
    ip_network("198.51.100.0/24"),
    ip_network("203.0.113.0/24"),
)


def load_scenarios():
    scenarios = {}
    for path in sorted(SCENARIOS_DIR.glob("*/scenario.json")):
        with path.open(encoding="utf-8") as file:
            scenario = json.load(file)
        scenarios[scenario["id"]] = scenario
    return scenarios


def load_expected():
    with FIXTURE_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def parse_iso_zoned(value):
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    assert parsed.tzinfo is not None, f"{value} must include timezone information"
    assert parsed.utcoffset() is not None, f"{value} must include a concrete UTC offset"
    return parsed


def walk_values(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from walk_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk_values(nested)
    elif isinstance(value, str):
        yield value


def assert_unique(values, label):
    assert len(values) == len(set(values)), f"duplicate {label}: {values}"


def assert_documentation_ip(value):
    parsed = ip_address(value)
    assert any(parsed in network for network in DOCUMENTATION_NETWORKS), (
        f"{value} must be from an RFC 5737 documentation range"
    )


def test_exactly_two_scenarios_exist_and_are_valid_json():
    paths = sorted(SCENARIOS_DIR.glob("*/scenario.json"))

    assert {path.parent.name for path in paths} == EXPECTED_SCENARIO_IDS

    scenarios = load_scenarios()
    assert set(scenarios) == EXPECTED_SCENARIO_IDS
    assert all(scenario_id == scenario["id"] for scenario_id, scenario in scenarios.items())


def test_scenarios_follow_contract_and_keep_expected_results_out():
    scenarios = load_scenarios()

    for scenario_id, scenario in scenarios.items():
        assert set(scenario) == SCENARIO_FIELDS
        assert scenario["synthetic"] is True
        assert isinstance(scenario["events"], list) and scenario["events"]
        assert isinstance(scenario["processes"], list) and scenario["processes"]
        assert isinstance(scenario["connections"], list) and scenario["connections"]
        assert isinstance(scenario["deployments"], list)

        visible_text = "\n".join(walk_values(scenario)).lower()
        for forbidden in FORBIDDEN_SCENARIO_TERMS:
            assert forbidden not in visible_text, f"{scenario_id} exposes answer term {forbidden!r}"

        for event in scenario["events"]:
            assert EVENT_FIELDS <= event.keys()
            assert set(event) <= EVENT_FIELDS | {"user", "ip", "pid"}
            parse_iso_zoned(event["timestamp"])
            if "ip" in event:
                assert_documentation_ip(event["ip"])

        for process in scenario["processes"]:
            assert set(process) == PROCESS_FIELDS
            assert isinstance(process["pid"], int)
            assert isinstance(process["parent_pid"], int)
            parse_iso_zoned(process["started_at"])

        for connection in scenario["connections"]:
            assert set(connection) == CONNECTION_FIELDS
            assert isinstance(connection["pid"], int)
            assert isinstance(connection["remote_port"], int)
            assert_documentation_ip(connection["remote_ip"])
            parse_iso_zoned(connection["timestamp"])

        for deployment in scenario["deployments"]:
            assert set(deployment) == DEPLOYMENT_FIELDS
            parse_iso_zoned(deployment["timestamp"])


def test_ids_are_unique_and_references_exist():
    for scenario_id, scenario in load_scenarios().items():
        event_ids = [event["id"] for event in scenario["events"]]
        process_keys = [(process["host"], process["pid"]) for process in scenario["processes"]]
        connection_ids = [connection["id"] for connection in scenario["connections"]]
        deployment_ids = [deployment["id"] for deployment in scenario["deployments"]]

        assert_unique(event_ids, f"{scenario_id} event ids")
        assert_unique(process_keys, f"{scenario_id} process host/pid keys")
        assert_unique(connection_ids, f"{scenario_id} connection ids")
        assert_unique(deployment_ids, f"{scenario_id} deployment ids")

        known_event_ids = set(event_ids)
        for collection_name in ("processes", "connections", "deployments"):
            for item in scenario[collection_name]:
                assert set(item["event_ids"]) <= known_event_ids, (
                    f"{scenario_id} {collection_name} references unknown events"
                )


def test_temporal_order_and_entity_correlations_are_coherent():
    for scenario_id, scenario in load_scenarios().items():
        events = {event["id"]: event for event in scenario["events"]}
        event_times = {event_id: parse_iso_zoned(event["timestamp"]) for event_id, event in events.items()}
        ordered_event_times = [event_times[event["id"]] for event in scenario["events"]]
        assert ordered_event_times == sorted(ordered_event_times), f"{scenario_id} events must be chronological"

        processes = {(process["host"], process["pid"]): process for process in scenario["processes"]}
        min_event_time = min(event_times.values())
        max_event_time = max(event_times.values())

        for process in scenario["processes"]:
            started_at = parse_iso_zoned(process["started_at"])
            assert min_event_time <= started_at <= max_event_time
            referenced = [events[event_id] for event_id in process["event_ids"]]
            assert any(event["host"] == process["host"] for event in referenced)
            assert any(event.get("user") == process["user"] for event in referenced)
            assert any(event.get("pid") in {process["pid"], process["parent_pid"]} for event in referenced)

        for connection in scenario["connections"]:
            process = processes[(connection["host"], connection["pid"])]
            connection_time = parse_iso_zoned(connection["timestamp"])
            assert connection_time >= parse_iso_zoned(process["started_at"])
            referenced = [events[event_id] for event_id in connection["event_ids"]]
            assert any(event.get("pid") == connection["pid"] for event in referenced)
            assert any(event.get("ip") == connection["remote_ip"] for event in referenced)
            assert all(event["host"] == connection["host"] for event in referenced)

        for deployment in scenario["deployments"]:
            referenced = [events[event_id] for event_id in deployment["event_ids"]]
            assert all(event["host"] == deployment["host"] for event in referenced)


def test_expected_fixtures_are_separate_and_reference_real_evidence():
    scenarios = load_scenarios()
    expected = load_expected()

    assert set(expected) == EXPECTED_SCENARIO_IDS
    for scenario_id, fixture in expected.items():
        scenario_text = json.dumps(scenarios[scenario_id], sort_keys=True).lower()
        assert fixture["expected_classification"] not in scenario_text
        assert fixture["expected_severity"] not in scenario_text

        event_ids = {event["id"] for event in scenarios[scenario_id]["events"]}
        connection_ids = {connection["id"] for connection in scenarios[scenario_id]["connections"]}
        deployment_ids = {deployment["id"] for deployment in scenarios[scenario_id]["deployments"]}
        evidence_ids = set(fixture["expected_evidence_ids"])

        assert evidence_ids <= event_ids | connection_ids | deployment_ids
        assert fixture["expected_classification"] in {"incident", "benign", "inconclusive"}
        assert fixture["expected_severity"] in {"info", "low", "medium", "high", "critical"}


def test_scenarios_do_not_share_evidence_or_entities_accidentally():
    scenarios = load_scenarios()
    ids_by_scenario = {}
    host_pid_by_scenario = {}

    for scenario_id, scenario in scenarios.items():
        ids_by_scenario[scenario_id] = (
            {event["id"] for event in scenario["events"]}
            | {connection["id"] for connection in scenario["connections"]}
            | {deployment["id"] for deployment in scenario["deployments"]}
        )
        host_pid_by_scenario[scenario_id] = {
            (process["host"], process["pid"]) for process in scenario["processes"]
        }

    assert ids_by_scenario["scenario-a"].isdisjoint(ids_by_scenario["scenario-b"])
    assert host_pid_by_scenario["scenario-a"].isdisjoint(host_pid_by_scenario["scenario-b"])


def test_ssh_scenario_correlates_authentication_process_and_connection():
    scenario = load_scenarios()["scenario-a"]
    expected = load_expected()["scenario-a"]["must_correlate"]
    events = scenario["events"]
    event_times = {event["id"]: parse_iso_zoned(event["timestamp"]) for event in events}

    correlated_events = [
        event
        for event in events
        if event["host"] == expected["host"] and event.get("user") == expected["user"]
    ]
    event_types = [event["event_type"] for event in correlated_events]
    sequence_positions = [event_types.index(event_type) for event_type in expected["sequence"]]
    assert sequence_positions == sorted(sequence_positions)

    process = next(
        process
        for process in scenario["processes"]
        if process["host"] == expected["host"] and process["pid"] == expected["pid"]
    )
    connection = next(
        connection
        for connection in scenario["connections"]
        if connection["host"] == expected["host"] and connection["pid"] == expected["pid"]
    )

    assert expected["remote_ip"] == connection["remote_ip"]
    assert parse_iso_zoned(process["started_at"]) < parse_iso_zoned(connection["timestamp"])
    assert event_times["evt-a-002"] < event_times["evt-a-005"] < event_times["evt-a-006"]


def test_administration_scenario_has_context_to_avoid_false_positive():
    scenario = load_scenarios()["scenario-b"]
    expected = load_expected()["scenario-b"]["must_correlate"]
    events = scenario["events"]
    event_types = [event["event_type"] for event in events]
    messages = " ".join(event["message"] for event in events)
    deployment_text = " ".join(deployment["description"] for deployment in scenario["deployments"])

    for event_type in expected["sequence"]:
        assert event_type in event_types

    assert event_types.index("auth_failure") < event_types.index("auth_success")
    assert event_types.index("change_window") < event_types.index("process_started")
    assert event_types.index("process_started") < event_types.index("network_connection")
    assert event_types.index("change_window") < event_types.index("deployment_completed")
    assert expected["change_id"] in messages
    assert expected["change_id"] in deployment_text

    admin_processes = [
        process
        for process in scenario["processes"]
        if process["host"] == expected["host"] and process["user"] == expected["user"]
    ]
    assert any(process["pid"] == expected["pid"] for process in admin_processes)
    assert any("/usr/bin/apt-get update" == process["command"] for process in admin_processes)


class ScenarioContractTests(unittest.TestCase):
    def test_exactly_two_scenarios_exist_and_are_valid_json(self):
        test_exactly_two_scenarios_exist_and_are_valid_json()

    def test_scenarios_follow_contract_and_keep_expected_results_out(self):
        test_scenarios_follow_contract_and_keep_expected_results_out()

    def test_ids_are_unique_and_references_exist(self):
        test_ids_are_unique_and_references_exist()

    def test_temporal_order_and_entity_correlations_are_coherent(self):
        test_temporal_order_and_entity_correlations_are_coherent()

    def test_expected_fixtures_are_separate_and_reference_real_evidence(self):
        test_expected_fixtures_are_separate_and_reference_real_evidence()

    def test_scenarios_do_not_share_evidence_or_entities_accidentally(self):
        test_scenarios_do_not_share_evidence_or_entities_accidentally()

    def test_ssh_scenario_correlates_authentication_process_and_connection(self):
        test_ssh_scenario_correlates_authentication_process_and_connection()

    def test_administration_scenario_has_context_to_avoid_false_positive(self):
        test_administration_scenario_has_context_to_avoid_false_positive()
