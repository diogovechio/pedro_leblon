intervals = (
    ('meses', 60 * 60 * 24 * 30),
    ('semanas', 60 * 60 * 24 * 7),
    ('dias', 60 * 60 * 24),
    ('horas', 60 * 60),
    ('minutos', 60),
    ('segundos', 1),
)


def display_time(
        seconds: int,
        granularity=6
) -> str:
    if seconds < 0:
        seconds *= -1

    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
                if name == "mese":
                    name = "mês"

            result.append("{} {}".format(value, name))

    joined = ', '.join(result[:granularity])
    last_comma_idx = joined.rfind(',')
    output = joined[:last_comma_idx] + ' e' + joined[last_comma_idx + 1:]
    return output
