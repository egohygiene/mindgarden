"""Read-only policy inspection over existing scope contracts."""

from ..domain.contracts import ContractRegistry, canonical_json, read_object
from ..domain.scope_policy import decide_scope, policy_capabilities
from ..domain.validation import ContractError


def run_policy(arguments):
    if arguments.operation == "inspect":
        result = policy_capabilities()
    else:
        if arguments.input.is_symlink():
            raise ContractError("SCOPE_REQUEST: policy input must be an explicit regular control file")
        request = read_object(arguments.input)
        if ContractRegistry().errors(request,"scope-request"):
            raise ContractError("SCOPE_REQUEST: supply a supported scope decision request")
        result = decide_scope(request["operation"],request["scopes"],destination=request.get("destination"),
                              review=request.get("review"),authority=request.get("authority"))
    print(canonical_json(result).decode(),end="")
    return 0 if result.get("outcome","allow") == "allow" else 3
