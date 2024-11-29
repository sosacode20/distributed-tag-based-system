from typing import Optional, Any, Callable
from pathlib import Path
import uuid
from pydantic import ValidatorFunctionWrapHandler
import os
import re


def match_binding(content: str) -> Optional[re.Match[str]]:
    """Match a valid binding of Docker"""
    path_re = r"[\.~]?(/[^/\\]+)+"
    # binding_re = f"{path_re}:{path_re}"
    binding_re = f"({path_re}):({path_re})"
    # print(binding_re)
    return re.fullmatch(binding_re, content)


def substitution_variable_rule(variable: str) -> str:
    res = "container_1" if variable == "name" else None
    assert res, f"The variable '{variable}' is unknown"
    return res


def substitution_environment_rule(variable: str) -> str:
    res = os.getenv(variable)
    assert res, f"There is no environment variable for {variable}"
    return res


def substitute(content: str, variable_rule: Callable[[str], str]) -> str:
    object_name = r"([a-zA-Z_-]+\w*)"
    # For properties like @{name}
    variable = r"@\{" + object_name + r"\}"
    environment_variable = r"\$\{" + object_name + r"\}"
    new_str = re.sub(variable, lambda m: variable_rule(m.group(1)), content)
    new_str = re.sub(
        environment_variable,
        lambda m: substitution_environment_rule(m.group(1)),
        new_str,
    )
    return new_str


def expand_variables(
    content: str,
    variable_rule: Callable[[str], str],
) -> str:
    """Expand variables of the form @{VARIABLE_NAME}"""
    object_name = r"([a-zA-Z_-]+\w*)"
    variable = r"@\{" + object_name + r"\}"
    new_str = re.sub(variable, lambda m: variable_rule(m.group(1)), content)
    return new_str


def expand_environment(content: str) -> str:
    """Expand environment variables of the form ${ENVIRONMENT_VARIABLE}"""
    object_name = r"([a-zA-Z_-]+\w*)"
    environment_variable = r"\$\{" + object_name + r"\}"
    new_str = re.sub(
        environment_variable,
        lambda m: substitution_environment_rule(m.group(1)),
        content,
    )
    return new_str


def validate_binding(
    binding: Any,
    # handler: ValidatorFunctionWrapHandler,
    # info: ValidationInfo,
) -> tuple[Path, Path]:
    assert isinstance(binding, str), f"'{binding}' for 'binding' is not a string"

    binding = expand_environment(binding)
    is_match = match_binding(binding)
    assert is_match, f"'{binding}' is NOT a valid binding"
    host_path, container_path = is_match.group(1), is_match.group(3)
    return Path(host_path), Path(container_path)


def generate_name(base_name: str) -> str:
    """Generate a unique name for the container"""
    id: str = uuid.uuid4().hex
    return f"{base_name}-{id}"
