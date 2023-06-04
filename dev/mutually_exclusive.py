import inspect
import sys


class MutuallyExclusiveArgsError(ValueError):
    ...


def mutually_exclusive(*mutually_exc_args_names: str):
    def wrapper(f):
        def inner(*args, **kwargs):
            bound_args = inspect.signature(f).bind(*args, **kwargs)
            bound_args.apply_defaults()
            validate(bound_args.arguments)
            return f(*args, **kwargs)

        def validate(kwargs: dict) -> None:
            mutually_exclusive_args_count = get_mutually_exc_args_count(kwargs)
            if mutually_exclusive_args_count != 1:
                raise MutuallyExclusiveArgsError("Mutually exclusive arguments must have exactly one value provided!")

        def get_mutually_exc_args_count(kwargs):
            mutually_exc_args_count = 0
            for arg_name, arg_val in kwargs.items():
                if arg_name in mutually_exc_args_names and arg_val is not None:
                    mutually_exc_args_count += 1
            return mutually_exc_args_count

        return inner

    return wrapper


sys.modules[__name__] = mutually_exclusive  # type: ignore
