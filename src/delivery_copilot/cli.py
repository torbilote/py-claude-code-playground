"""Command-line interface for Delivery Copilot.

Usage examples:
    delivery-copilot engagement list
    delivery-copilot engagement show eng-abc123
    delivery-copilot engagement add --client "Acme Corp" --name "Platform Migration" --lead "j.doe@valtech.com"
    delivery-copilot risk add eng-abc123 --description "Vendor API deprecation" --severity high --owner "j.doe@valtech.com"
    delivery-copilot time log eng-abc123 --consultant "j.doe@valtech.com" --hours 4.5 --note "Sprint planning"
    delivery-copilot report status eng-abc123
"""

from __future__ import annotations

import click

from delivery_copilot import store


@click.group()
def cli() -> None:
    """Delivery Copilot: manage client engagements, risks, tasks, and time."""


@cli.group()
def engagement() -> None:
    """Manage engagements."""


@engagement.command("list")
def engagement_list() -> None:
    engagements = store.load_engagements()
    if not engagements:
        click.echo("No engagements yet. Try `delivery-copilot engagement add`.")
        return
    for e in engagements:
        open_risks = len(e.open_risks())
        flag = f" [!] {open_risks} open risk(s)" if open_risks else ""
        click.echo(f"{e.id}  [{e.status}]  {e.client_name} - {e.name} (lead: {e.lead}){flag}")


@engagement.command("show")
@click.argument("engagement_id")
def engagement_show(engagement_id: str) -> None:
    e = store.get_engagement(engagement_id)
    if not e:
        raise click.ClickException(f"No engagement found with id '{engagement_id}'")
    click.echo(f"{e.id} - {e.client_name}: {e.name}")
    click.echo(f"  status: {e.status}   lead: {e.lead}   started: {e.start_date}")
    click.echo(f"  total logged hours: {e.total_hours()}")
    click.echo(f"  tasks ({len(e.tasks)}):")
    for t in e.tasks:
        click.echo(f"    - [{t.status}] {t.title} (assignee: {t.assignee}, due {t.due_date})")
    click.echo(f"  risks ({len(e.risks)}):")
    for r in e.risks:
        click.echo(f"    - [{r.status}/{r.severity}] {r.description} (owner: {r.owner})")


@engagement.command("add")
@click.option("--client", "client_name", required=True, help="Client name")
@click.option("--name", required=True, help="Engagement / project name")
@click.option("--lead", required=True, help="Engagement lead email")
@click.option("--start-date", default=None, help="ISO date, defaults to today")
def engagement_add(client_name: str, name: str, lead: str, start_date: str | None) -> None:
    e = store.add_engagement(client_name=client_name, name=name, lead=lead, start_date=start_date)
    click.echo(f"Created engagement {e.id}")


@cli.group()
def risk() -> None:
    """Manage engagement risks."""


@risk.command("add")
@click.argument("engagement_id")
@click.option("--description", required=True)
@click.option("--severity", type=click.Choice(["low", "medium", "high"]), required=True)
@click.option("--owner", required=True)
def risk_add(engagement_id: str, description: str, severity: str, owner: str) -> None:
    r = store.add_risk(engagement_id, description=description, severity=severity, owner=owner)
    if not r:
        raise click.ClickException(f"No engagement found with id '{engagement_id}'")
    click.echo(f"Added risk {r.id} to {engagement_id}")


@risk.command("mitigate")
@click.argument("engagement_id")
@click.argument("risk_id")
@click.option("--mitigation", required=True, help="Description of the mitigation applied")
def risk_mitigate(engagement_id: str, risk_id: str, mitigation: str) -> None:
    ok = store.mitigate_risk(engagement_id, risk_id, mitigation)
    if not ok:
        raise click.ClickException(f"Could not find risk '{risk_id}' on engagement '{engagement_id}'")
    click.echo(f"Marked {risk_id} as mitigated")


@cli.group()
def task() -> None:
    """Manage engagement tasks."""


@task.command("add")
@click.argument("engagement_id")
@click.option("--title", required=True)
@click.option("--assignee", required=True)
@click.option("--due-date", required=True)
def task_add(engagement_id: str, title: str, assignee: str, due_date: str) -> None:
    t = store.add_task(engagement_id, title=title, assignee=assignee, due_date=due_date)
    if not t:
        raise click.ClickException(f"No engagement found with id '{engagement_id}'")
    click.echo(f"Added task {t.id} to {engagement_id}")


@cli.group()
def time() -> None:
    """Log time against an engagement."""


@time.command("log")
@click.argument("engagement_id")
@click.option("--consultant", required=True, help="Consultant email")
@click.option("--hours", required=True, type=float)
@click.option("--note", default="")
@click.option("--task-id", default=None)
def time_log(engagement_id: str, consultant: str, hours: float, note: str, task_id: str | None) -> None:
    entry = store.log_time(engagement_id, consultant=consultant, hours=hours, note=note, task_id=task_id)
    if not entry:
        raise click.ClickException(f"No engagement found with id '{engagement_id}'")
    click.echo(f"Logged {hours}h for {consultant} on {engagement_id}")


@cli.group()
def report() -> None:
    """Generate reports."""


@report.command("status")
@click.argument("engagement_id")
def report_status(engagement_id: str) -> None:
    """Print a client-ready status report. See the `status-report` skill for the polished version."""
    e = store.get_engagement(engagement_id)
    if not e:
        raise click.ClickException(f"No engagement found with id '{engagement_id}'")
    click.echo(f"# Status Report - {e.client_name}: {e.name}\n")
    click.echo(f"Overall status: **{e.status}**")
    click.echo(f"Hours logged to date: {e.total_hours()}\n")
    open_risks = e.open_risks()
    click.echo(f"## Risks ({len(open_risks)} open)")
    for r in open_risks:
        click.echo(f"- [{r.severity}] {r.description} (owner: {r.owner})")
    click.echo("\n## Tasks in flight")
    for t in e.tasks:
        if t.status != "done":
            click.echo(f"- [{t.status}] {t.title} (due {t.due_date}, {t.assignee})")


if __name__ == "__main__":
    cli()
