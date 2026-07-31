import re
from dataclasses import dataclass
from typing import Any

from notifications.models import NotificationTemplate

VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


@dataclass
class RenderedNotification:
    subject: str
    title: str
    body: str
    variables: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "title": self.title,
            "body": self.body,
            "variables": self.variables,
        }


def resolve_path(context: dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    value: Any = context
    for part in parts:
        if isinstance(value, dict):
            if part not in value:
                return ""
            value = value[part]
        else:
            value = getattr(value, part, "")
        if callable(value):
            value = value()
    return value


def collect_variables(
    template: NotificationTemplate, context: dict[str, Any]
) -> dict[str, str]:
    variables: dict[str, str] = {}
    for name, path in template.variable_mapping.items():
        value = context[name] if name in context else resolve_path(context, path)
        variables[name] = "" if value is None else str(value)

    referenced = set(
        VARIABLE_PATTERN.findall(
            "\n".join([template.subject, template.title, template.body])
        )
    )
    for name in referenced:
        if name not in variables:
            value = context.get(name, "")
            variables[name] = "" if value is None else str(value)
    return variables


def render_text(value: str, variables: dict[str, str]) -> str:
    return VARIABLE_PATTERN.sub(lambda match: variables.get(match.group(1), ""), value)


def render_notification(
    template: NotificationTemplate, context: dict[str, Any]
) -> RenderedNotification:
    variables = collect_variables(template, context)
    return RenderedNotification(
        subject=render_text(template.subject, variables),
        title=render_text(template.title, variables),
        body=render_text(template.body, variables),
        variables=variables,
    )
