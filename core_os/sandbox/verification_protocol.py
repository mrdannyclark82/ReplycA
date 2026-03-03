import ast
from core_os.sandbox.security_policy import SecurityPolicy

class VerificationProtocol:
    """
    Performs static analysis on Python code to ensure it adheres to the
    SecurityPolicy.
    """
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    def verify_script(self, code: str) -> bool:
        """
        Parses the code into an AST and checks for violations.
        Returns True if safe, False otherwise.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # If code isn't valid Python, it's not "safe" to run (or rather, it won't run)
            return False

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self.policy.is_module_allowed(alias.name):
                        return False
            elif isinstance(node, ast.ImportFrom):
                if node.module and not self.policy.is_module_allowed(node.module):
                    return False
        
        return True
