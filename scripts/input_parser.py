import shlex

def auto_convert(value):
    value = value.strip()
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value

def parse_args(args_string):
    tokens = shlex.split(args_string)
    result = {}
    key = None
    values = []

    for token in tokens:
        if token.startswith("--"):
            if key:
                # Adiciona como lista apenas se houver mais de 1 valor
                result[key] = (
                    [auto_convert(v) for v in values] if len(values) > 1 else
                    auto_convert(values[0]) if values else True
                )
            key = token[2:]
            values = []
        else:
            values.append(token)

    if key:
        result[key] = (
            [auto_convert(v) for v in values] if len(values) > 1 else
            auto_convert(values[0]) if values else True
        )

    return result

def parse_paths_string(paths_string):
    paths = paths_string.strip().split()