import re
from rich import print
from typing import Optional
import os


def match_path(content: str):
    path_re = r"[\.~]?(/[^/\\]+)+"
    return re.fullmatch(path_re, content)


def substitution_variable_rule(variable: str) -> str:
    res = "container_1" if variable == "name" else None
    assert res, f"The variable '{variable}' is unknown"
    return res


def substitution_environment_rule(variable: str) -> str:
    res = os.getenv(variable)
    assert res, f"There is no environment variable for {variable}"
    return res


def substitute(content: str) -> str:
    object_name = r"([a-zA-Z_-]+\w*)"
    # For properties like @{name}
    variable = r"@\{" + object_name + r"\}"
    environment_variable = r"\$\{" + object_name + r"\}"
    new_str = re.sub(
        variable, lambda m: substitution_variable_rule(m.group(1)), content
    )
    new_str = re.sub(
        environment_variable,
        lambda m: substitution_environment_rule(m.group(1)),
        new_str,
    )
    return new_str


def match_binding(content: str) -> Optional[re.Match[str]]:
    """Match a valid binding of Docker"""
    path_re = r"[\.~]?(/[^/\\]+)+"
    binding_re = f"({path_re}):({path_re})"
    print(binding_re)
    return re.fullmatch(binding_re, content)


bindings = [
    r"./downloaded/clients/@{name}",  # invalid
    r"./downloaded/clients/@{name",  # invalid
    r"downloaded/clients/@{name}",  # invalid
    r"./downloaded/clients/@{name}:/app/downloaded",  # valid
    r"./downloaded/clients/@{name}:/app/downloaded-${USER}",  # valid
    r"downloaded/clients/@{name}:/app/downloaded",  # invalid
    r"~/downloaded/clients/@{name}:app/downloaded",  # invalid
    r"~/downloaded/clients:/app/downloaded",
]

for binding in bindings:
    is_match = match_binding(binding)
    if is_match:
        print(f"'{binding}' is a valid binding")
        new_str = substitute(binding)
        print(f"'{binding}' transforms into -> '{new_str}'")
    else:
        print(f"'{binding}' is not a valid binding")
        new_str = substitute(binding)
        print(f"'{binding}' transforms into -> '{new_str}'")
