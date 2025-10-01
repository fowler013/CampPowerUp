#!/usr/bin/env python3
"""
Debug syntax errors in the app.py file
"""

def find_syntax_error():
    try:
        with open('registration_form/app.py', 'r') as f:
            content = f.read()
        
        # Try to compile the entire file
        compile(content, 'registration_form/app.py', 'exec')
        print("✅ No syntax errors found!")
        
    except SyntaxError as e:
        print(f"❌ Syntax error found:")
        print(f"  Line {e.lineno}: {e.text.strip() if e.text else 'N/A'}")
        print(f"  Error: {e.msg}")
        print(f"  Position: {' ' * (e.offset - 1) if e.offset else ''}^")
        
        # Try to find the context around the error
        lines = content.split('\n')
        start = max(0, e.lineno - 5)
        end = min(len(lines), e.lineno + 5)
        
        print(f"\nContext around line {e.lineno}:")
        for i in range(start, end):
            marker = ">>> " if i + 1 == e.lineno else "    "
            print(f"{marker}{i + 1:4d}: {lines[i]}")
    
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    find_syntax_error()