"""Darwin extended-ACL checks for ordinary single-user registry controls.

Public API constants/semantics were checked against Apple Libc source
71bbe350ab79eef58113991d817ccc6165061a64, sys/acl.h and posix1e manuals.
This bridge uses the native API; no Apple implementation is copied here.
"""

import ctypes
import errno
from functools import lru_cache
import sys

from ..domain.validation import ContractError

ACL_TYPE_EXTENDED = 0x00000100
ACL_FIRST_ENTRY = 0


@lru_cache(maxsize=1)
def native_acl_api():
    """Cache function bindings only, never user ACLs or authorization results."""
    try:
        library = ctypes.CDLL(None, use_errno=True)
        library.acl_get_fd_np.argtypes = [ctypes.c_int, ctypes.c_int]
        library.acl_get_fd_np.restype = ctypes.c_void_p
        library.acl_valid.argtypes = [ctypes.c_void_p]
        library.acl_valid.restype = ctypes.c_int
        library.acl_get_entry.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
        library.acl_get_entry.restype = ctypes.c_int
        library.acl_free.argtypes = [ctypes.c_void_p]
        library.acl_free.restype = ctypes.c_int
        return library
    except (AttributeError, OSError) as error:
        raise ContractError("REGISTRY_PLATFORM: native extended-ACL verification is unavailable") from error


def require_native_acl_support() -> None:
    if sys.platform == "darwin": native_acl_api()


def require_no_extended_acl(descriptor: int) -> None:
    """Reject every extended entry, including restrictive ones, without modifying it."""
    if sys.platform != "darwin": return
    api = native_acl_api()
    ctypes.set_errno(0)
    acl = api.acl_get_fd_np(descriptor, ACL_TYPE_EXTENDED)
    if not acl:
        # Darwin filesec_get_property reports ENOENT for an absent ACL property.
        # The file itself is already open and checked by the control adapter.
        if ctypes.get_errno() == errno.ENOENT: return
        raise ContractError("REGISTRY_ACL_UNAVAILABLE: registry access permissions cannot be verified")
    try:
        if api.acl_valid(acl) != 0:
            raise ContractError("REGISTRY_ACL_UNAVAILABLE: native registry ACL is invalid")
        entry = ctypes.c_void_p()
        ctypes.set_errno(0)
        result = api.acl_get_entry(acl, ACL_FIRST_ENTRY, ctypes.byref(entry))
        if result == 0:
            raise ContractError("REGISTRY_ACL: extended ACL entries are unsupported on private registry controls; review permissions locally")
        if result != -1 or ctypes.get_errno() != errno.EINVAL:
            raise ContractError("REGISTRY_ACL_UNAVAILABLE: registry ACL entries cannot be verified")
        # A validated native ACL with no first entry is empty on Darwin.
    finally:
        if api.acl_free(acl) != 0:
            raise ContractError("REGISTRY_ACL_UNAVAILABLE: native ACL verification did not complete")
