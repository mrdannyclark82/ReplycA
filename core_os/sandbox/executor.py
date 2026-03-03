from typing import Optional, Any, Dict
from core_os.sandbox.verification_protocol import VerificationProtocol

class ExecutionResult:
    """Stores the result of a sandboxed execution."""
    def __init__(
        self, 
        success: bool, 
        output: str = "", 
        error: Optional[str] = None,
        locals: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.output = output
        self.error = error
        self.locals = locals or {}

class SandboxExecutor:
    """
    Executes Python code in a controlled environment after verification.
    """
    def __init__(self, verifier: VerificationProtocol, timeout: float = 30.0):
        self.verifier = verifier
        self.timeout = timeout
        self.db_path = None

    def set_db_path(self, db_path: str):
        """Sets the database path and initializes the table."""
        import sqlite3
        import os
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                code TEXT,
                success BOOLEAN,
                output TEXT,
                error TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def _log_execution(self, code: str, result: ExecutionResult):
        """Logs the execution result to the database."""
        if not self.db_path:
            return
        
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tool_executions (code, success, output, error)
                VALUES (?, ?, ?, ?)
            ''', (code, result.success, result.output, result.error))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Failed to log execution: {e}")

    def execute(self, code: str) -> ExecutionResult:
        """
        Verifies and then executes the provided code, capturing stdout and stderr.
        Enforces a timeout.
        """
        import io
        import signal
        from contextlib import redirect_stdout, redirect_stderr

        if not self.verifier.verify_script(code):
            result = ExecutionResult(success=False, error="Security verification failed.")
            self._log_execution(code, result)
            return result

        def timeout_handler(signum, frame):
            raise TimeoutError("Execution timed out.")

        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        # Set the timeout handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        # Use alarm (int seconds only for alarm, so we round up)
        signal.alarm(max(1, int(self.timeout + 0.9)))

        result = None
        try:
            exec_locals: Dict[str, Any] = {}
            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                exec(code, {"__builtins__": __builtins__}, exec_locals)
            result = ExecutionResult(
                success=True, 
                output=output_buffer.getvalue(), 
                error=error_buffer.getvalue() if error_buffer.getvalue() else None,
                locals=exec_locals
            )
        except TimeoutError as e:
            result = ExecutionResult(
                success=False,
                output=output_buffer.getvalue(),
                error=str(e)
            )
        except Exception as e:
            result = ExecutionResult(
                success=False, 
                output=output_buffer.getvalue(), 
                error=error_buffer.getvalue() + str(e)
            )
        finally:
            # Disable the alarm and restore original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            
        if result:
            self._log_execution(code, result)
        return result
