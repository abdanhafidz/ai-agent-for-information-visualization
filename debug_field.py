from sqlmodel import Field
import inspect

try:
    sig = inspect.signature(Field)
    print("sa_type" in sig.parameters)
except ImportError:
    print("ImportError")
