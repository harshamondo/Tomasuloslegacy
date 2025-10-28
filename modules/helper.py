def _get_alias_str(alias_obj):
    if isinstance(alias_obj, str):
        return alias_obj
    return getattr(alias_obj, "current_alias", None)

def is_arf(alias_obj) -> bool:
    alias = _get_alias_str(alias_obj)
    return isinstance(alias, str) and alias.startswith("ARF")