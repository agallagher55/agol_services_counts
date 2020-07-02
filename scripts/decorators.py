"""
Decorators
- Function Name
- TimeStamp
- Errors
"""

import functools
import datetime
import time
import arcpy


def debug(callback):

    @functools.wraps(callback)
    def wrapper(*args, **kwargs):
        print(f"\nRunning: '{callback.__name__}' function... {datetime.datetime.now().strftime('%H:%M:%S - %m/%d/%Y')}")

        if len(args) > 0:
            print(f"Args: {', '.join([str(arg) for arg in args])}")

        if len(list(kwargs.keys())) > 0:
            print(f"Kwargs: {[f'{k}: {v}' for k, v in kwargs.items()]}")

        try:
            value = callback(*args, **kwargs)
            return value

        except arcpy.ExecuteError:
            print(f"\t!ARCPY ERROR: {arcpy.GetMessages(2)}")

        except Exception as e:
            print(f"\tERROR: {e}")

    return wrapper


def logger(func):
    import logging
    logging.basicConfig(filename=f'{func.__name__}.log', level=logging.INFO)
    print(f"Logging: {func.__name__}...")

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(
            f'Ran {func.__name__} with args: ({", ".join([str(a) for a in args] + [f"{k}: {v}" for k, v in kwargs.items()])})'
        )
        result = func(*args, **kwargs)
        logging.info(f'Result: {result}')
        logging.info(datetime.datetime.now())
        return result
    return wrapper


def timer(func):
    func_name = func.__name__
    print(f"\nDecorating {func_name} function at {datetime.datetime.now()}...")

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        print(
            f"\tRunning {func_name} function at {datetime.datetime.now()}...")

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        run_time = end_time - start_time
        print(f"\t{func_name} function finished running in {run_time:.5f} seconds.")

        # Important to return the return value of the decorated function
        return result

    return wrapper


if __name__ == "__main__":
    @logger
    def say_hello(name):
        print(f"Creating Greeting...")
        return f"HELLO, {name}"


    # Decorate function, prepare function
    # greet_alex = say_hello('alex')

    # Run function
    print(say_hello(name='alex'))