import datetime
import io
import json
import logging
import pathlib
import sys
import urllib.parse as urlparse
from lib.issue import issue_from_dict

import sarif_om as om
from jschema_to_python.to_json import to_json

LOG = logging.getLogger(__name__)

TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def extract_from_file(tool_name, report_file):
    """Extract properties from reports

    :param tool_name: tool name
    :param report_file: Report file
    :return issues, metrics, skips information
    """
    issues = []
    metrics = {}
    skips = []
    with io.open(report_file, "r") as rfile:
        if pathlib.PurePosixPath(report_file).suffix == ".json":
            report_data = json.loads(rfile.read())
            # NodeJsScan uses sec_issues
            if "sec_issues" in report_data:
                sec_data = report_data["sec_issues"]
                for key, value in sec_data.items():
                    if isinstance(value, list):
                        issues = issues + value
                    else:
                        issues = issues.append(value)
            if "total_count" in report_data:
                metrics["total_count"] = report_data["total_count"]
            if "vuln_count" in report_data:
                metrics["vuln_count"] = report_data["vuln_count"]
    return issues, metrics, skips


def convert_file(tool_name, tool_args, report_file, converted_file):
    """Convert report file

    :param tool_name: tool name
    :param tool_args: tool args
    :param report_file: Report file
    :param converted_file: Converted file

    :return serialized_log: SARIF output data
    """
    issues, metrics, skips = extract_from_file(tool_name, report_file)
    return report(tool_name, tool_args, metrics, skips, issues, converted_file)


def report(tool_name, tool_args, metrics, skips, issues, crep_fname):
    """Prints issues in SARIF format

    :param tool_name: tool name
    :param tool_args: Args used for the tool
    :param metrics: metrics data
    :param skips: skips data
    :param issues: issues data
    :param crep_fname: The output file name

    :return serialized_log: SARIF output data
    """
    if not tool_args:
        tool_args = ""
    log = om.SarifLog(
        schema_uri="https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        version="2.1.0",
        runs=[
            om.Run(
                tool=om.Tool(driver=om.ToolComponent(name=tool_name)),
                invocations=[
                    om.Invocation(
                        end_time_utc=datetime.datetime.utcnow().strftime(
                            TS_FORMAT
                        ),
                        execution_successful=True,
                    )
                ],
                conversion={"tool": om.Tool(driver=om.ToolComponent(name="@AppThreat/sast-scan")), "invocation": tool_args},
                properties={"metrics": metrics},
            )
        ],
    )

    run = log.runs[0]
    invocation = run.invocations[0]

    add_skipped_file_notifications(skips, invocation)
    add_results(issues, run)

    serialized_log = to_json(log)

    if crep_fname:
        with io.open(crep_fname, "w") as fileobj:
            fileobj.write(serialized_log)

        if fileobj.name != sys.stdout.name:
            LOG.info("SARIF output written to file: %s", fileobj.name)
    return serialized_log


def add_skipped_file_notifications(skips, invocation):
    if skips is None or len(skips) == 0:
        return

    if invocation.tool_configuration_notifications is None:
        invocation.tool_configuration_notifications = []

    for skip in skips:
        (file_name, reason) = skip

        notification = om.Notification(
            level="error",
            message=om.Message(text=reason),
            locations=[
                om.Location(
                    physical_location=om.PhysicalLocation(
                        artifact_location=om.ArtifactLocation(
                            uri=to_uri(file_name)
                        )
                    )
                )
            ],
        )

        invocation.tool_configuration_notifications.append(notification)


def add_results(issues, run):
    """Method to convert issues into results schema

    :param issues: Issues found
    :param run: Run object
    """
    if run.results is None:
        run.results = []

    rules = {}
    rule_indices = {}
    for issue in issues:
        result = create_result(issue, rules, rule_indices)
        run.results.append(result)

    if len(rules) > 0:
        run.tool.driver.rules = list(rules.values())


def create_result(issue, rules, rule_indices):
    """Method to convert a single issue into result schema with rules

    :param issue: Issues object
    :param rules: List of rules
    :param rule_indices: Indices of referred rules
    """
    if isinstance(issue, dict):
        issue = issue_from_dict(issue)

    issue_dict = issue.as_dict()

    rule, rule_index = create_or_find_rule(issue_dict, rules, rule_indices)

    physical_location = om.PhysicalLocation(
        artifact_location=om.ArtifactLocation(
            uri=to_uri(issue_dict["filename"])
        )
    )

    add_region_and_context_region(
        physical_location, issue_dict["line_number"], issue_dict["code"]
    )

    return om.Result(
        rule_id=rule.id,
        rule_index=rule_index,
        message=om.Message(text=issue_dict["issue_text"]),
        level=level_from_severity(issue_dict["issue_severity"]),
        locations=[om.Location(physical_location=physical_location)],
        properties={
            "issue_confidence": issue_dict["issue_confidence"],
            "issue_severity": issue_dict["issue_severity"],
        },
    )


def level_from_severity(severity):
    if severity == "HIGH":
        return "error"
    elif severity == "MEDIUM":
        return "warning"
    elif severity == "LOW":
        return "note"
    else:
        return "warning"


def add_region_and_context_region(physical_location, line_number, code):
    snippet_lines = code.split("\n")
    snippet_line = snippet_lines[0]

    physical_location.region = om.Region(
        start_line=line_number, snippet=om.ArtifactContent(text=snippet_line)
    )

    physical_location.context_region = om.Region(
        start_line=line_number,
        end_line=line_number + len(snippet_lines) - 1,
        snippet=om.ArtifactContent(text="".join(snippet_lines)),
    )


def get_url(rule_id):
    return rule_id


def create_or_find_rule(issue_dict, rules, rule_indices):
    rule_id = issue_dict["test_id"]
    if rule_id in rules:
        return rules[rule_id], rule_indices[rule_id]

    rule = om.ReportingDescriptor(
        id=rule_id, name=issue_dict["test_name"], help_uri=get_url(rule_id),
    )

    index = len(rules)
    rules[rule_id] = rule
    rule_indices[rule_id] = index
    return rule, index


def to_uri(file_path):
    pure_path = pathlib.PurePath(file_path)
    if pure_path.is_absolute():
        return pure_path.as_uri()
    else:
        posix_path = pure_path.as_posix()  # Replace backslashes with slashes.
        return urlparse.quote(posix_path)  # %-encode special characters.
