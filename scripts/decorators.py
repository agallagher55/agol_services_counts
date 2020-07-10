import functools
import datetime
import traceback
import arcpy


def logger(callback):
    @functools.wraps(callback)
    def wrapper(*args, **kwargs):
        print(f"\nRunning: '{callback.__name__}' function... {datetime.datetime.now().strftime('%H:%M:%S - %m/%d/%Y')}")

        if len(args) > 0:
            print(f"Args: {args}")
        if len(list(kwargs.keys())) > 0:
            print(f"Kwargs: {['{}: {}'.format(k, v) for k, v in kwargs.items() if v is not None]}")
        try:
            value = callback(*args, **kwargs)
            return value

        except arcpy.ExecuteError:
            print(f"\t!ARCPY ERROR: {arcpy.GetMessages(2)}")

        except Exception as e:
            print(f"\tERROR: {e}")
            print(traceback.format_exc())

    return wrapper
