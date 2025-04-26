import importlib
import sys
import inspect
import datetime

def check_function_exists(module_path, function_name):
    try:
        module = importlib.import_module(module_path)
        if hasattr(module, function_name):
            function = getattr(module, function_name)
            # Get function signature if possible
            try:
                signature = str(inspect.signature(function))
                return True, signature
            except (ValueError, TypeError):
                # If we can't get signature, just return that it exists
                return True, "Unable to determine signature"
        else:
            return False, None
    except ImportError:
        return False, None
    except Exception as e:
        print(f"Error checking {module_path}.{function_name}: {e}")
        return False, None

# List of functions to check
functions_to_check = [
    ("aiter.fused_moe_bf16_asm", "moe_sorting_ck"),
    ("aiter.fused_moe_bf16_asm", "asm_moe"),
    ("aiter.fused_moe_bf16_asm", "ck_moe_2stages")
]

# Check each function
missing_functions = []
changed_functions = []
unchanged_functions = []

# Load previous signatures if available
previous_signatures = {}
try:
    with open("function_signatures.txt", "r") as f:
        for line in f:
            if line.strip():
                parts = line.strip().split(" | ")
                if len(parts) == 3:
                    func_path, func_name, signature = parts
                    previous_signatures[f"{func_path}.{func_name}"] = signature
except FileNotFoundError:
    # No previous signatures file
    pass

# Check current functions and compare with previous state
current_signatures = {}
for module_path, function_name in functions_to_check:
    full_path = f"{module_path}.{function_name}"
    exists, signature = check_function_exists(module_path, function_name)

    if exists:
        current_signatures[full_path] = signature if signature else "Unknown"

        if full_path in previous_signatures:
            if previous_signatures[full_path] != signature:
                changed_functions.append((full_path, previous_signatures[full_path], signature))
            else:
                unchanged_functions.append(full_path)
        else:
            # First time seeing this function
            unchanged_functions.append(full_path)
    else:
        missing_functions.append(full_path)

# Save current signatures for future comparison
with open("function_signatures.txt", "w") as f:
    for module_path, function_name in functions_to_check:
        full_path = f"{module_path}.{function_name}"
        if full_path in current_signatures:
            f.write(f"{module_path} | {function_name} | {current_signatures[full_path]}\n")

# Report results
print(f"API Check Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

if not missing_functions and not changed_functions:
    print("✅ All functions exist and signatures are unchanged.")
    print("\nFunctions checked:")
    for func in unchanged_functions:
        print(f"- {func}: {current_signatures.get(func, 'Unknown')}")
    sys.exit(0)
else:
    print("⚠️ API CHANGES DETECTED")
    print("\nDetails:")

    if missing_functions:
        print("\n🔴 Missing Functions:")
        for func in missing_functions:
            print(f"- {func}")

    if changed_functions:
        print("\n🟠 Changed Function Signatures:")
        for func, old_sig, new_sig in changed_functions:
            print(f"- {func}:")
            print(f"  Old: {old_sig}")
            print(f"  New: {new_sig}")

    if unchanged_functions:
        print("\n🟢 Unchanged Functions:")
        for func in unchanged_functions:
            print(f"- {func}: {current_signatures.get(func, 'Unknown')}")

    sys.exit(1)
