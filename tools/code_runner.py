import io
import contextlib


def run_python(code: str):

    output = io.StringIO()

    try:
        with contextlib.redirect_stdout(output):

            exec(
                code,
                {"__builtins__": {}},
                {}
            )

        return output.getvalue()

    except Exception as e:
        return f"Execution error: {e}"