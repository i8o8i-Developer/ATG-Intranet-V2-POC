import py_compile
import sys

try:
    py_compile.compile(r"c:\Users\i8o8i\Desktop\INTRANET\ReBuild\INTRANET\Backend\EnterpriseCore\management\commands\Seed_Demo_Erp.py", doraise=True)
    print("Syntax OK")
except Exception as e:
    print("Syntax Error:", e)
